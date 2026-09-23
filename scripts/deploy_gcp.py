"""Create/update a dedicated low-cost Cloud Run deployment. No credentials in source."""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
REGION = "us-central1"


class Deployment:
    def __init__(self, project, dry_run=False, notification_email=None):
        self.project = project
        self.dry = dry_run
        self.notification_email = notification_email
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

    def api(self, method, url, payload=None, *, sample=None):
        """Use the already-authenticated CLI identity; tokens stay out of logs/files."""
        print(f"+ {method} {url}", flush=True)
        if self.dry:
            return sample or {}
        token = self.run("auth", "print-access-token")
        response = httpx.request(method, url, json=payload,
                                 headers={"Authorization": f"Bearer {token}",
                                          "x-goog-user-project": self.project}, timeout=60)
        if not response.is_success:
            raise RuntimeError(f"Cloud API failed ({response.status_code}): {response.text[:1000]}")
        return response.json() if response.content else {}

    def ensure(self, describe, create):
        if self.run(*describe, optional=True) is None or self.dry:
            self.run(*create)

    def deploy(self, *, defer_scheduler=False, image=None):
        project = self.project
        archive = f"{project}-sc-jail-data"
        builds = f"{project}-sc-jail-builds"
        build_image = image is None
        image = image or f"{REGION}-docker.pkg.dev/{project}/sc-jail/app:latest"
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
            "storagetransfer.googleapis.com",
            "monitoring.googleapis.com",
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
            self.run("storage", "buckets", "update", f"gs://{bucket}",
                     "--soft-delete-duration=7d" if bucket == archive else "--soft-delete-duration=0",
                     "--uniform-bucket-level-access", "--public-access-prevention")
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
        for bucket, role in ((builds, "builder"),):
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
        self.protect_archive(archive, accounts["collector"])
        self.configure_backup(archive)
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
        if build_image:
            self.run(
                "builds", "submit", ".", "--config", "cloudbuild.yaml",
                "--service-account", f"projects/{project}/serviceAccounts/{accounts['builder']}",
                "--gcs-source-staging-dir", f"gs://{builds}/source",
                "--gcs-log-dir", f"gs://{builds}/logs", "--region", REGION,
                "--substitutions", f"_IMAGE={image},_REVISION={self.source_revision()}",
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
                f"--update-env-vars=SCJ_BUCKET={archive}",
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
        self.configure_monitoring(urls["dashboard"])
        if not defer_scheduler:
            self.configure_scheduler(urls["collector"])
        else:
            print("Services prepared. Scheduler has not been configured or invoked.")
            print("Migrate local history, then rerun with --scheduler-only to start collection.")
        print("Dashboard:", urls["dashboard"])
        print("Archive:", f"gs://{archive}")
        print("Free allowances are shared. Set a small billing alert; it is not a spending cap.")

    @staticmethod
    def source_revision():
        # Includes uncommitted release content when deployment precedes the commit.
        import hashlib

        digest = hashlib.sha256()
        for path in sorted((ROOT / "src" / "sc_jail").rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(ROOT).as_posix().encode())
                digest.update(path.read_bytes())
        return "source-" + digest.hexdigest()[:20]

    def protect_archive(self, archive, collector):
        prefix = f"projects/_/buckets/{archive}/objects/"
        member = f"serviceAccount:{collector}"
        for role in ("roles/storage.objectViewer", "roles/storage.objectCreator"):
            self.run("storage", "buckets", "add-iam-policy-binding", f"gs://{archive}",
                     "--member", member, "--role", role, "--condition=None")
        expression = " || ".join(
            f"resource.name.startsWith('{prefix}{part}')"
            for part in ("public/", "private/checkpoints/", "private/analytics/")
        ) + f" || resource.name == '{prefix}private/collector-lease.json'"
        self.run("storage", "buckets", "add-iam-policy-binding", f"gs://{archive}",
                 "--member", member, "--role", "roles/storage.objectAdmin",
                 "--condition", "title=mutable-projections-only,expression=" + expression)
        policy = json.loads(self.run("storage", "buckets", "get-iam-policy", f"gs://{archive}",
                                     "--format=json", sample='{"bindings": []}'))
        if any(b["role"] == "roles/storage.objectAdmin" and not b.get("condition")
               and member in b["members"] for b in policy.get("bindings", [])):
            self.run("storage", "buckets", "remove-iam-policy-binding", f"gs://{archive}",
                     "--member", member, "--role", "roles/storage.objectAdmin", "--condition=None")

    def configure_backup(self, archive):
        backup = f"{self.project}-sc-jail-backup"
        self.ensure(["storage", "buckets", "describe", f"gs://{backup}"],
                    ["storage", "buckets", "create", f"gs://{backup}", "--location", REGION,
                     "--uniform-bucket-level-access", "--public-access-prevention"])
        self.run("storage", "buckets", "update", f"gs://{backup}", "--versioning",
                 "--soft-delete-duration=7d", "--uniform-bucket-level-access",
                 "--public-access-prevention", "--lifecycle-file=deploy/backup-lifecycle.json")
        base = "https://storagetransfer.googleapis.com/v1"
        agent = self.api("GET", f"{base}/googleServiceAccounts/{self.project}",
                         sample={"accountEmail": "transfer-agent@example.test"})["accountEmail"]
        for bucket, roles in ((archive, ("roles/storage.objectViewer", "roles/storage.legacyBucketReader")),
                              (backup, ("roles/storage.objectAdmin", "roles/storage.legacyBucketReader"))):
            for role in roles:
                self.run("storage", "buckets", "add-iam-policy-binding", f"gs://{bucket}",
                         "--member", f"serviceAccount:{agent}", "--role", role, "--condition=None")
        description = "sc-jail daily archive backup"
        query = str(httpx.QueryParams({"filter": json.dumps({"projectId": self.project})}))
        jobs = self.api("GET", f"{base}/transferJobs?{query}")
        existing = next((j for j in jobs.get("transferJobs", [])
                         if j.get("description") == description and j.get("status") != "DELETED"), None)
        today = datetime.now(timezone.utc).date()
        job = {"projectId": self.project, "description": description, "status": "ENABLED",
               "transferSpec": {"gcsDataSource": {"bucketName": archive},
                                "gcsDataSink": {"bucketName": backup},
                                "objectConditions": {"excludePrefixes": ["private/collector-lease.json"]},
                                "transferOptions": {"overwriteWhen": "DIFFERENT",
                                                    "deleteObjectsUniqueInSink": False}},
               "loggingConfig": {"logActions": ["COPY", "FIND"], "logActionStates": ["FAILED"]},
               "schedule": {"scheduleStartDate": {"year": today.year, "month": today.month,
                                                   "day": today.day},
                            "startTimeOfDay": {"hours": 5, "minutes": 10}}}
        if existing:
            mutable = {key: job[key] for key in ("transferSpec", "schedule", "status", "loggingConfig")}
            self.api("PATCH", f"{base}/{existing['name']}",
                     {"projectId": self.project, "transferJob": mutable,
                      "updateTransferJobFieldMask": "transferSpec,schedule,status,loggingConfig"})
        else:
            self.api("POST", f"{base}/transferJobs", job)

    def configure_monitoring(self, dashboard_url):
        base = f"https://monitoring.googleapis.com/v3/projects/{self.project}"
        checks = self.api("GET", base + "/uptimeCheckConfigs").get("uptimeCheckConfigs", [])
        policies = self.api("GET", base + "/alertPolicies").get("alertPolicies", [])
        channels = self.api("GET", base + "/notificationChannels").get("notificationChannels", [])
        if self.notification_email and not any(
            c.get("type") == "email" and c.get("labels", {}).get("email_address") == self.notification_email
            and c.get("enabled", True) for c in channels
        ):
            channels.append(self.api("POST", base + "/notificationChannels", {
                "type": "email", "displayName": "sc-jail operator", "enabled": True,
                "labels": {"email_address": self.notification_email},
            }, sample={"name": f"projects/{self.project}/notificationChannels/operator", "enabled": True}))
        channel_names = [c["name"] for c in channels if c.get("enabled", True)]
        for product in ("population", "iml_details", "xfer_courts", "repeat_visits"):
            title = f"sc-jail {product} freshness"
            path = "/api/freshness" + ("" if product == "population" else "/" + product)
            check = next((c for c in checks if c["displayName"] == title), None)
            if check is None:
                check = self.api("POST", base + "/uptimeCheckConfigs", {
                    "displayName": title, "monitoredResource": {"type": "uptime_url", "labels": {
                        "project_id": self.project, "host": urlparse(dashboard_url).netloc}},
                    "httpCheck": {"path": path, "port": 443, "useSsl": True, "validateSsl": True},
                    "period": "300s", "timeout": "30s", "selectedRegions": ["USA"],
                }, sample={"name": f"projects/{self.project}/uptimeCheckConfigs/{product}"})
            check_id = check["name"].rsplit("/", 1)[-1]
            policy = {"displayName": title, "combiner": "OR", "enabled": True,
                      "notificationChannels": channel_names,
                      "conditions": [{"displayName": title, "conditionThreshold": {
                          "filter": 'resource.type="uptime_url" AND '
                                    'metric.type="monitoring.googleapis.com/uptime_check/check_passed" '
                                    f'AND metric.label.check_id="{check_id}"',
                          "comparison": "COMPARISON_GT", "thresholdValue": 1, "duration": "900s",
                          "aggregations": [{"alignmentPeriod": "300s", "perSeriesAligner": "ALIGN_NEXT_OLDER",
                                            "crossSeriesReducer": "REDUCE_COUNT_FALSE",
                                            "groupByFields": ["resource.label.host"]}],
                      }}]}
            prior = next((p for p in policies if p["displayName"] == title), None)
            self.api("PATCH" if prior else "POST",
                     "https://monitoring.googleapis.com/v3/" + prior["name"] if prior else base + "/alertPolicies",
                     policy)
        title = "sc-jail backup failure"
        policy = {"displayName": title, "combiner": "OR", "enabled": True,
                  "notificationChannels": channel_names,
                  "conditions": [{"displayName": title, "conditionMatchedLog": {
                      "filter": 'resource.type="storage_transfer_job" AND severity>=ERROR',
                  }}],
                  "alertStrategy": {"notificationRateLimit": {"period": "3600s"},
                                    "autoClose": "86400s"}}
        prior = next((p for p in policies if p["displayName"] == title), None)
        self.api("PATCH" if prior else "POST",
                 "https://monitoring.googleapis.com/v3/" + prior["name"] if prior else base + "/alertPolicies",
                 policy)
        if not channel_names:
            print("Freshness and backup incidents are enabled in Cloud Monitoring; "
                  "no notification channel is configured.")

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
    parser.add_argument("--notification-email", help="Create an enabled email channel for operational alerts")
    parser.add_argument("--image", help="Deploy an already verified image digest without rebuilding")
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
    if args.image and not re.fullmatch(
        re.escape(f"{REGION}-docker.pkg.dev/{args.project}/sc-jail/app@sha256:") + r"[0-9a-f]{64}",
        args.image,
    ):
        parser.error("--image must be an immutable digest in this project's sc-jail/app repository")
    deployment = Deployment(args.project, args.dry_run, notification_email=args.notification_email)
    if args.scheduler_only:
        deployment.configure_scheduler()
    else:
        deployment.deploy(defer_scheduler=args.defer_scheduler, image=args.image)


if __name__ == "__main__":
    main()
