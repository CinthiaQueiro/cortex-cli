import subprocess
from pathlib import Path

import typer


def run(
    base: str = typer.Option("main", "--base", "-b", help="Branch base para comparar (ex: main, develop)"),
    output: str = typer.Option(None, "--output", "-o", help="Arquivo para salvar a descrição gerada"),
) -> None:
    """Gera uma descrição de PR a partir dos commits e arquivos alterados em relação a uma branch base."""
    commits = _git(["log", f"{base}..HEAD", "--pretty=format:%s"])
    stat = _git(["diff", "--stat", f"{base}...HEAD"])

    if not commits.strip() and not stat.strip():
        typer.echo(f"Nenhuma diferença encontrada entre HEAD e '{base}'.")
        raise typer.Exit(code=1)

    description = _build_description(commits, stat)

    if output:
        Path(output).write_text(description, encoding="utf-8")
        typer.echo(f"Descrição salva em {output}")
    else:
        typer.echo(description)


def _git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(result.stderr, err=True)
        raise typer.Exit(code=1)
    return result.stdout


def _build_description(commits: str, stat: str) -> str:
    commit_lines = [line for line in commits.splitlines() if line.strip()]
    stat_lines = [line for line in stat.splitlines() if line.strip()]

    summary = "\n".join(f"- {line}" for line in commit_lines) or "- (sem commits novos)"
    files = "\n".join(f"- {line.strip()}" for line in stat_lines) or "- (sem arquivos alterados)"

    return (
        "## Resumo\n"
        f"{summary}\n\n"
        "## Arquivos alterados\n"
        f"{files}\n"
    )
