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
