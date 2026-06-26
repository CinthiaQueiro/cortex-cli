import os
from dataclasses import dataclass

from dotenv import load_dotenv


def load_config() -> None:
    # override=False: variáveis já presentes no ambiente (ex: injetadas pelo
    # pipeline PowerShell em dev/tst/prd) sempre têm prioridade sobre o .env local.
    load_dotenv(override=False)


@dataclass
class AzureDevOpsConfig:
    org: str
    project: str
    pat: str


def get_azure_devops_config() -> AzureDevOpsConfig:
    org = os.environ.get("AZURE_DEVOPS_ORG")
    project = os.environ.get("AZURE_DEVOPS_PROJECT")
    pat = os.environ.get("AZURE_DEVOPS_PAT")

    missing = [
        name
        for name, value in (
            ("AZURE_DEVOPS_ORG", org),
            ("AZURE_DEVOPS_PROJECT", project),
            ("AZURE_DEVOPS_PAT", pat),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Variáveis de ambiente faltando: {', '.join(missing)}. "
            "Configure-as no .env (dev) ou nas variáveis do pipeline (tst/prd)."
        )

    return AzureDevOpsConfig(org=org, project=project, pat=pat)
