import base64

import requests
import typer

from core.config import get_azure_devops_config

API_VERSION = "7.1"


def run(
    title: str = typer.Option(..., "--title", "-t", help="Título do card"),
    work_item_type: str = typer.Option(
        "Task", "--type", help="Tipo do work item: Task, User Story, Bug, etc."
    ),
    description: str = typer.Option(None, "--description", "-d", help="Descrição do card"),
    area_path: str = typer.Option(None, "--area-path", help="Area Path do projeto"),
    iteration_path: str = typer.Option(None, "--iteration-path", help="Iteration Path (sprint)"),
    assigned_to: str = typer.Option(None, "--assigned-to", help="E-mail da pessoa responsável"),
) -> None:
    """Cria um work item (Task, User Story, Bug, etc.) em um board do Azure DevOps."""
    try:
        config = get_azure_devops_config()
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    fields = {"/fields/System.Title": title}
    if description:
        fields["/fields/System.Description"] = description
    if area_path:
        fields["/fields/System.AreaPath"] = area_path
    if iteration_path:
        fields["/fields/System.IterationPath"] = iteration_path
    if assigned_to:
        fields["/fields/System.AssignedTo"] = assigned_to

    patch = [{"op": "add", "path": path, "value": value} for path, value in fields.items()]

    url = (
        f"https://dev.azure.com/{config.org}/{config.project}/_apis/wit/workitems/"
        f"${work_item_type}?api-version={API_VERSION}"
    )
    auth_token = base64.b64encode(f":{config.pat}".encode()).decode()
    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {auth_token}",
    }

    response = requests.post(url, json=patch, headers=headers)
    if not response.ok:
        typer.echo(f"Erro ao criar card ({response.status_code}): {response.text}", err=True)
        raise typer.Exit(code=1)

    card = response.json()
    typer.echo(f"Card criado: #{card['id']} - {card['fields']['System.Title']}")
    typer.echo(card["_links"]["html"]["href"])
