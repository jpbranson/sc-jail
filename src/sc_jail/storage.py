"""Atomic local objects and generation-checked private Cloud Storage objects."""

import gzip
import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import ContextManager, Protocol

from filelock import FileLock, Timeout


class Conflict(RuntimeError):
    pass


class Store(Protocol):
    """Object versions are opaque; callers never depend on a backend client."""

    def read(self, key: str) -> tuple[bytes | None, object]: ...
    def write(self, key: str, content: bytes, expected=None, *, create_only=False): ...
    def keys(self, prefix: str) -> list[str]: ...
    def lease(self, *, renewable=False) -> ContextManager: ...


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class LocalStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        parts = PurePosixPath(key)
        if parts.is_absolute() or ".." in parts.parts or "\\" in key:
            raise ValueError("Invalid object key")
        result = self.root.joinpath(*parts.parts).resolve()
        if not result.is_relative_to(self.root):
            raise ValueError("Object key escaped storage")
        return result

    def read(self, key):
        try:
            content = self.path(key).read_bytes()
            return content, hashlib.sha256(content).hexdigest()
        except FileNotFoundError:
            return None, None

    def write(self, key, content, expected=None, *, create_only=False):
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self.root / ".objects.lock"), timeout=10):
            old, version = self.read(key)
            if create_only and old is not None:
                return version
            if not create_only and version != expected:
                raise Conflict("Object changed concurrently")
            temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
            try:
                with temp.open("wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
        return hashlib.sha256(content).hexdigest()

    def keys(self, prefix):
        return sorted(
            path.relative_to(self.root).as_posix()
            for path in self.path(prefix).rglob("*")
            if path.is_file() and not path.name.endswith(".tmp")
        )

    @contextmanager
    def lease(self, *, renewable=False):
        try:
            with FileLock(str(self.root / ".collector.lock"), timeout=0):
                yield
        except Timeout as exc:
            raise Conflict("Another collector is running") from exc


class GCSStore:
    def __init__(self, bucket):
        from google.cloud import storage

        self.bucket = storage.Client().bucket(bucket)
        self._lease_expires = None
        self._renewable = False
        from google.api_core.retry import Retry

        self._retry = Retry(initial=1, maximum=3, deadline=20)

    def read(self, key):
        from google.api_core.exceptions import NotFound, PreconditionFailed

        if key != "private/collector-lease.json":
            self._maintain_lease()
        for _ in range(3):
            blob = self.bucket.blob(key)
            try:
                blob.reload(timeout=20, retry=self._retry)
                return blob.download_as_bytes(
                    if_generation_match=blob.generation, timeout=20, retry=self._retry
                ), blob.generation
            except NotFound:
                return None, None
            except PreconditionFailed:
                continue
        raise Conflict("Object kept changing during read")

    def write(self, key, content, expected=None, *, create_only=False):
        from google.api_core.exceptions import NotFound, PreconditionFailed

        if key != "private/collector-lease.json":
            self._maintain_lease()
        if (
            key != "private/collector-lease.json"
            and self._lease_expires is not None
            and time.time() + 60 >= self._lease_expires
        ):
            raise Conflict("Collector lease is too close to expiry to commit safely")
        blob = self.bucket.blob(key)
        if create_only:
            # The routine collector cannot overwrite historical objects. Avoid
            # requesting overwrite permissions merely to deduplicate existing bytes.
            try:
                blob.reload(timeout=20, retry=self._retry)
                return blob.generation
            except NotFound:
                pass
        try:
            blob.upload_from_string(
                content,
                content_type="application/octet-stream",
                if_generation_match=0 if create_only else (expected or 0),
                timeout=20,
                retry=self._retry,
            )
            return blob.generation
        except PreconditionFailed as exc:
            if create_only:
                return None  # Immutable, deterministic key already exists.
            raise Conflict("Object changed concurrently") from exc

    def keys(self, prefix):
        self._maintain_lease()
        keys = []
        for blob in self.bucket.list_blobs(prefix=prefix, timeout=20, retry=self._retry):
            self._maintain_lease()
            keys.append(blob.name)
        return sorted(keys)

    def _maintain_lease(self):
        if not getattr(self, "_renewable", False) or self._lease_expires is None:
            return
        moment = time.time()
        if moment + 60 >= self._lease_expires:
            raise Conflict("Maintenance lease expired before it could be renewed")
        if moment + 180 < self._lease_expires:
            return
        expires = moment + 660
        self._lease_generation = self.write(
            "private/collector-lease.json",
            encode({"owner": self._lease_owner, "expires": expires}),
            expected=self._lease_generation,
        )
        self._lease_expires = expires

    @contextmanager
    def lease(self, *, renewable=False):
        key = "private/collector-lease.json"
        old, generation = self.read(key)
        if old and json.loads(old)["expires"] > time.time():
            raise Conflict("Another collector is running")
        expires = time.time() + 660
        self._lease_owner = uuid.uuid4().hex
        generation = self.write(
            key, encode({"owner": self._lease_owner, "expires": expires}), expected=generation
        )
        self._lease_expires = expires
        self._lease_generation = generation
        self._renewable = renewable
        try:
            yield
        finally:
            self._lease_expires = None
            self._renewable = False
            try:
                self.write(key, encode({"expires": 0}), expected=self._lease_generation)
            except Conflict:
                pass  # Never release a newer owner's lease.


def make_store(config):
    return GCSStore(config.bucket) if config.bucket else LocalStore(config.data_dir)


def read_json(store, key, default=None):
    raw, version = store.read(key)
    if raw is None:
        return default, version
    if key.endswith(".gz"):
        raw = gzip.decompress(raw)
    return json.loads(raw), version


def write_json(store, key, value, *, expected=None, create_only=False):
    raw = encode(value)
    if key.endswith(".gz"):
        raw = gzip.compress(raw, mtime=0)
    return store.write(key, raw, expected=expected, create_only=create_only)


def archive_blob(store, name, content):
    digest = hashlib.sha256(content).hexdigest()
    key = f"private/blobs/{digest[:2]}/{digest}.gz"
    compressed = gzip.compress(content, mtime=0)
    store.write(key, compressed, create_only=True)
    return {
        "name": name,
        "key": key,
        "sha256": digest,
        "bytes": len(content),
        "compressed_bytes": len(compressed),
    }
