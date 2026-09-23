import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "deploy_gcp", Path(__file__).resolve().parents[1] / "scripts" / "deploy_gcp.py"
)
deploy_gcp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy_gcp)


class RecordingDeployment(deploy_gcp.Deployment):
    def __init__(self):
        super().__init__("sc-jail-test", dry_run=True)
        self.dry = False
        self.commands = []

    def run(self, *args, optional=False, sample=""):
        self.commands.append(args)
        if args[:3] == ("billing", "projects", "describe"):
            return '{"billingEnabled": true}'
        return None if optional else sample

    def api(self, method, url, payload=None, *, sample=None):
        self.commands.append(("api", method, url, payload))
        return sample or {}


def test_preparing_services_cannot_start_collection_before_history_migration():
    deployment = RecordingDeployment()
    deployment.deploy(defer_scheduler=True)

    services = [command[2] for command in deployment.commands if command[:2] == ("run", "deploy")]
    assert services == ["sc-jail-collector", "sc-jail-dashboard"]
    assert not any(command[0] == "scheduler" for command in deployment.commands)


def test_activation_uses_existing_services_without_rebuilding_or_changing_storage():
    deployment = RecordingDeployment()
    deployment.configure_scheduler()

    assert not any(
        command[0] in {"builds", "storage", "artifacts"} or command[:2] == ("run", "deploy")
        for command in deployment.commands
    )
    create = next(
        command for command in deployment.commands if command[:3] == ("scheduler", "jobs", "create")
    )
    assert create[create.index("--uri") + 1] == "https://sc-jail-collector-EXAMPLE.run.app/collect"
    assert create[create.index("--oidc-token-audience") + 1] == (
        "https://sc-jail-collector-EXAMPLE.run.app"
    )
    assert any(command[:3] == ("scheduler", "jobs", "run") for command in deployment.commands)


def test_fresh_service_account_binding_retries_propagation_delay(monkeypatch):
    deployment = deploy_gcp.Deployment("sc-jail-test", dry_run=True)
    deployment.dry = False
    replies = iter(
        [
            deploy_gcp.subprocess.CompletedProcess(
                [], 1, "", "HTTPError 400: Service account scj-builder does not exist."
            ),
            deploy_gcp.subprocess.CompletedProcess([], 0, "bound", ""),
        ]
    )
    waits = []
    monkeypatch.setattr(deploy_gcp.subprocess, "run", lambda *args, **kwargs: next(replies))
    monkeypatch.setattr(deploy_gcp.time, "sleep", waits.append)

    assert deployment.run("storage", "buckets", "add-iam-policy-binding") == "bound"
    assert waits == [5]


def test_deployment_preserves_tuning_and_protects_archive():
    deployment = RecordingDeployment()
    deployment.deploy(defer_scheduler=True)
    commands = deployment.commands
    for command in commands:
        if command[:2] == ("run", "deploy"):
            assert any(a.startswith("--update-env-vars=SCJ_BUCKET=") for a in command)
            assert not any(a.startswith("--set-env-vars") for a in command)
        if command[:3] == ("storage", "buckets", "update") and command[3].endswith("-sc-jail-data"):
            assert "--soft-delete-duration=7d" in command
    collector_admin = [c for c in commands if "roles/storage.objectAdmin" in c
                       and "serviceAccount:scj-collector@sc-jail-test.iam.gserviceaccount.com" in c]
    assert len(collector_admin) == 1
    assert "mutable-projections-only" in collector_admin[0][-1]
    backup = next(c[3] for c in commands if c[:2] == ("api", "POST") and c[2].endswith("/transferJobs"))
    assert backup["transferSpec"]["transferOptions"]["deleteObjectsUniqueInSink"] is False
    assert backup["transferSpec"]["gcsDataSink"]["bucketName"].endswith("-sc-jail-backup")
    assert backup["loggingConfig"]["logActionStates"] == ["FAILED"]
    policies = [c[3] for c in commands if c[:2] == ("api", "POST") and c[2].endswith("/alertPolicies")]
    assert len(policies) == 5
    assert any("conditionMatchedLog" in p["conditions"][0] for p in policies)


def test_operational_email_channel_attaches_to_all_alerts():
    deployment = RecordingDeployment()
    deployment.notification_email = "operator@example.test"
    deployment.configure_monitoring("https://dashboard.example.test")
    channel = next(c[3] for c in deployment.commands
                   if c[:2] == ("api", "POST") and c[2].endswith("/notificationChannels"))
    assert channel["labels"]["email_address"] == "operator@example.test"
    policies = [c[3] for c in deployment.commands
                if c[:2] == ("api", "POST") and c[2].endswith("/alertPolicies")]
    assert len(policies) == 5
    assert all(p["notificationChannels"] == ["projects/sc-jail-test/notificationChannels/operator"]
               for p in policies)


def test_verified_image_can_deploy_without_rebuilding_during_maintenance():
    deployment = RecordingDeployment()
    image = "us-central1-docker.pkg.dev/sc-jail-test/sc-jail/app@sha256:" + "1" * 64
    deployment.deploy(defer_scheduler=True, image=image)
    assert not any(c[:2] == ("builds", "submit") for c in deployment.commands)
    deployments = [c for c in deployment.commands if c[:2] == ("run", "deploy")]
    assert len(deployments) == 2
    assert all(c[c.index("--image") + 1] == image for c in deployments)


def test_backup_update_omits_immutable_project_identifier():
    deployment = RecordingDeployment()
    original_api = deployment.api

    def api(method, url, payload=None, *, sample=None):
        if method == "GET" and "/transferJobs?" in url:
            return {"transferJobs": [{"name": "transferJobs/example", "status": "ENABLED",
                                      "description": "sc-jail daily archive backup"}]}
        return original_api(method, url, payload, sample=sample)

    deployment.api = api
    deployment.configure_backup("sc-jail-test-sc-jail-data")
    patch = next(c[3] for c in deployment.commands if c[:2] == ("api", "PATCH"))
    assert patch["projectId"] == "sc-jail-test"
    assert set(patch["transferJob"]) == {"transferSpec", "schedule", "status", "loggingConfig"}
