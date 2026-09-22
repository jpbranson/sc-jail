"""Create/update a dedicated low-cost Cloud Run deployment. No credentials in source."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGION = "us-central1"


class Deployment:
    def __init__(self, project, dry_run=False):
        self.project = project
        self.dry = dry_run
        self.gcloud = shutil.which("gcloud") or "gcloud"
        if not dry_run and not shutil.which("gcloud"):
            raise SystemExit("Install Google Cloud CLI and run gcloud auth login first.")

    def run(self, *args, optional=False, sample=""):
        command = [self.gcloud, *args, "--project", self.project, "--quiet"]
        print("+", subprocess.list2cmdline(command), flush=True)
        if self.dry:
            return sample
        for attempt in range(5):
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            pending_account = (
                args[:3] == ("storage", "buckets", "add-iam-policy-binding")
                and "Service account" in result.stderr
                and "does not exist" in result.stderr
            )
            if not result.returncode or not pending_account or attempt == 4:
                break
            delay = 5 * 2**attempt
            print(f"Waiting {delay}s for the new service account to propagate.", flush=True)
            time.sleep(delay)
        if result.returncode:
            if optional:
                return None
            sys.stderr.write(result.stderr)
            raise SystemExit(result.returncode)
        return result.stdout.strip()

    def ensure(self, describe, create):
        if self.run(*describe, optional=True) is None or self.dry:
            self.run(*create)

    def deploy(self, *, defer_scheduler=False):
        project = self.project
        archive = f"{project}-sc-jail-data"
        builds = f"{project}-sc-jail-builds"
        image = f"{REGION}-docker.pkg.dev/{project}/sc-jail/app:latest"
        if not self.dry:
            billing = json.loads(
                self.run("billing", "projects", "describe", project, "--format=json")
            )
            if not billing.get("billingEnabled"):
                raise SystemExit("Enable billing for the selected project before deploying.")
        self.run(
            "services",
            "enable",
            "run.googleapis.com",
            "cloudscheduler.googleapis.com",
            "storage.googleapis.com",
            "artifactregistry.googleapis.com",
            "cloudbuild.googleapis.com",
            "iam.googleapis.com",
        )
        for bucket in (archive, builds):
            self.ensure(
                ["storage", "buckets", "describe", f"gs://{bucket}"],
                [
                    "storage",
                    "buckets",
                    "create",
                    f"gs://{bucket}",
                    "--location",
                    REGION,
                    "--uniform-bucket-level-access",
                    "--public-access-prevention",
                ],
            )
            self.run("storage", "buckets", "update", f"gs://{bucket}", "--soft-delete-duration=0")
        self.run(
            "storage",
            "buckets",
            "update",
            f"gs://{builds}",
            "--lifecycle-file=deploy/build-lifecycle.json",
        )
        self.ensure(
            ["artifacts", "repositories", "describe", "sc-jail", "--location", REGION],
            [
                "artifacts",
                "repositories",
                "create",
                "sc-jail",
                "--repository-format=docker",
                "--location",
                REGION,
            ],
        )
        self.run(
            "artifacts",
            "repositories",
            "set-cleanup-policies",
            "sc-jail",
            "--location",
            REGION,
            "--policy=deploy/image-cleanup.json",
            "--no-dry-run",
        )
        accounts = {
            role: f"scj-{role}@{project}.iam.gserviceaccount.com"
            for role in ("collector", "dashboard", "scheduler", "builder")
        }
        for role, email in accounts.items():
            self.ensure(
                ["iam", "service-accounts", "describe", email],
                [
                    "iam",
                    "service-accounts",
                    "create",
                    f"scj-{role}",
                    "--display-name",
                    f"Shelby jail {role}",
                ],
            )
        for bucket, role in ((archive, "collector"), (builds, "builder")):
            self.run(
                "storage",
                "buckets",
                "add-iam-policy-binding",
                f"gs://{bucket}",
                "--member",
                f"serviceAccount:{accounts[role]}",
                "--role",
                "roles/storage.objectAdmin",
                "--condition=None",
            )
        # Cloud Build validates bucket metadata before reading source or writing logs.
        self.run(
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{builds}",
            "--member",
            f"serviceAccount:{accounts['builder']}",
            "--role",
            "roles/storage.legacyBucketReader",
            "--condition=None",
        )
        self.run(
            "storage",
            "buckets",
            "add-iam-policy-binding",
            f"gs://{archive}",
            "--member",
            f"serviceAccount:{accounts['dashboard']}",
            "--role",
            "roles/storage.objectViewer",
            "--condition",
            "title=aggregate-only,expression=resource.name.startsWith("
            f"'projects/_/buckets/{archive}/objects/public/')",
        )
        self.run(
            "artifacts",
            "repositories",
            "add-iam-policy-binding",
            "sc-jail",
            "--location",
            REGION,
            "--member",
            f"serviceAccount:{accounts['builder']}",
            "--role",
            "roles/artifactregistry.writer",
        )
        self.run(
            "builds",
            "submit",
            ".",
            "--config",
            "cloudbuild.yaml",
            "--service-account",
            f"projects/{project}/serviceAccounts/{accounts['builder']}",
            "--gcs-source-staging-dir",
            f"gs://{builds}/source",
            "--gcs-log-dir",
            f"gs://{builds}/logs",
            "--region",
            REGION,
            "--substitutions",
            f"_IMAGE={image}",
        )
        urls = {}
        for role in ("collector", "dashboard"):
            service = f"sc-jail-{role}"
            self.run(
                "run",
                "deploy",
                service,
                "--image",
                image,
                "--region",
                REGION,
                "--service-account",
                accounts[role],
                "--cpu=0.25",
                "--memory=512Mi",
                "--concurrency=1",
                "--min-instances=0",
                "--max-instances=1",
                "--execution-environment=gen1",
                "--timeout=600" if role == "collector" else "--timeout=60",
                "--cpu-throttling",
                "--no-cpu-boost",
                "--port=8080",
                "--command=python",
                f"--args=-m,sc_jail,{role},--host,0.0.0.0,--port,8080",
                f"--set-env-vars=SCJ_BUCKET={archive}",
                "--allow-unauthenticated" if role == "dashboard" else "--no-allow-unauthenticated",
            )
            urls[role] = self.run(
                "run",
                "services",
                "describe",
                service,
                "--region",
                REGION,
                "--format=value(status.url)",
                sample=f"https://sc-jail-{role}-EXAMPLE.run.app",
            )
        if not defer_scheduler:
            self.configure_scheduler(urls["collector"])
        else:
            print("Services prepared. Scheduler has not been configured or invoked.")
            print("Migrate local history, then rerun with --scheduler-only to start collection.")
        print("Dashboard:", urls["dashboard"])
        print("Archive:", f"gs://{archive}")
        print("Free allowances are shared. Set a small billing alert; it is not a spending cap.")

    def configure_scheduler(self, collector_url=None):
        if collector_url is None:
            collector_url = self.run(
                "run",
                "services",
                "describe",
                "sc-jail-collector",
                "--region",
                REGION,
                "--format=value(status.url)",
                sample="https://sc-jail-collector-EXAMPLE.run.app",
            )
        scheduler_account = f"scj-scheduler@{self.project}.iam.gserviceaccount.com"
        self.run(
            "run",
            "services",
            "add-iam-policy-binding",
            "sc-jail-collector",
            "--region",
            REGION,
            "--member",
            f"serviceAccount:{scheduler_account}",
            "--role",
            "roles/run.invoker",
        )
        job_exists = self.run(
            "scheduler",
            "jobs",
            "describe",
            "sc-jail-quarter-hour",
            "--location",
            REGION,
            optional=True,
        )
        action = "update" if job_exists is not None and not self.dry else "create"
        self.run(
            "scheduler",
            "jobs",
            action,
            "http",
            "sc-jail-quarter-hour",
            "--location",
            REGION,
            "--schedule=*/15 * * * *",
            "--time-zone=UTC",
            "--uri",
            collector_url + "/collect",
            "--http-method=POST",
            "--oidc-service-account-email",
            scheduler_account,
            "--oidc-token-audience",
            collector_url,
            "--attempt-deadline=600s",
            "--max-retry-attempts=2",
            "--max-retry-duration=600s",
            "--min-backoff=60s",
            "--max-backoff=120s",
        )
        if not self.dry:
            self.run("scheduler", "jobs", "run", "sc-jail-quarter-hour", "--location", REGION)
            print("Collection started. Wait for a complete collection, then check /api/status.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project", required=True, help="Existing Google Cloud project with billing enabled"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands; make no cloud changes"
    )
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument(
        "--defer-scheduler",
        action="store_true",
        help="For a new deployment, prepare services without configuring or running Scheduler",
    )
    stage.add_argument(
        "--scheduler-only",
        action="store_true",
        help="Configure and invoke Scheduler for existing services after history migration",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", args.project):
        parser.error("Invalid Google Cloud project ID")
    deployment = Deployment(args.project, args.dry_run)
    if args.scheduler_only:
        deployment.configure_scheduler()
    else:
        deployment.deploy(defer_scheduler=args.defer_scheduler)


if __name__ == "__main__":
    main()
