import re
from pathlib import Path

import anthropic
import typer

from core.config import get_anthropic_api_key

MODEL = "claude-sonnet-4-6"


def run(
    file: str = typer.Option(..., "--file", "-f", help="Caminho do arquivo Python para gerar testes"),
    output: str = typer.Option(None, "--output", "-o", help="Caminho para salvar o arquivo de teste gerado"),
) -> None:
    """Gera testes automatizados (pytest) para um arquivo Python usando IA."""
    source_path = Path(file)
    if not source_path.is_file():
        typer.echo(f"Arquivo não encontrado: {file}", err=True)
        raise typer.Exit(code=1)

    try:
        api_key = get_anthropic_api_key()
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc

    source_code = source_path.read_text(encoding="utf-8")
    test_code = _generate_tests(api_key, source_path.name, source_code)

    if output:
        Path(output).write_text(test_code, encoding="utf-8")
        typer.echo(f"Testes salvos em {output}")
    else:
        typer.echo(test_code)


def _generate_tests(api_key: str, file_name: str, source_code: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Gere testes automatizados usando pytest para o código Python abaixo. "
        "Cubra o caminho feliz e os principais casos de borda. "
        "Responda apenas com o código do arquivo de teste, sem explicações.\n\n"
        f"Arquivo: {file_name}\n\n"
        f"```python\n{source_code}\n```"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_code_fence(response.content[0].text)


def _strip_code_fence(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*)```", text, re.DOTALL)
    return match.group(1).strip() + "\n" if match else text.strip() + "\n"
