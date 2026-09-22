"""Bounded HTTP sessions for the two county hosts."""

import ssl
import time

import httpx


class SourceError(RuntimeError):
    pass


class SourceHTTP:
    def __init__(self, base_url, *, user_agent, budget=240):
        self.deadline = time.monotonic() + budget
        context = ssl.create_default_context()
        # Both county appliances lack RFC 5746 support. Allow the initial legacy
        # handshake for these dedicated sessions only; certificate/hostname
        # verification and the TLS >= 1.2 minimum remain enabled.
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        self.client = httpx.Client(
            base_url=base_url,
            verify=context,
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def request(self, method, path, *, max_bytes=25_000_000, **kwargs):
        for attempt in range(3):
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise SourceError("Source collection exceeded its time budget")
            try:
                timeout = httpx.Timeout(min(20, remaining), connect=min(10, remaining))
                with self.client.stream(method, path, timeout=timeout, **kwargs) as response:
                    if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                        delay = min(
                            15,
                            int(response.headers.get("Retry-After", "2"))
                            if response.headers.get("Retry-After", "2").isdigit()
                            else 2 ** (attempt + 1),
                        )
                        if delay >= self.deadline - time.monotonic():
                            raise SourceError("Source retry would exceed the time budget")
                        time.sleep(delay)
                        continue
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > max_bytes:
                            raise SourceError("Source response exceeded the configured size limit")
                        if time.monotonic() >= self.deadline:
                            raise SourceError("Source collection exceeded its time budget")
                        chunks.append(chunk)
                    return httpx.Response(
                        response.status_code,
                        content=b"".join(chunks),
                        headers={
                            k: v
                            for k, v in response.headers.items()
                            if k.lower() not in {"content-encoding", "content-length"}
                        },
                        request=response.request,
                    )
            except httpx.TransportError:
                if attempt == 2:
                    raise
                time.sleep(min(2**attempt, max(0, self.deadline - time.monotonic())))
        raise SourceError("Retry budget exhausted")
