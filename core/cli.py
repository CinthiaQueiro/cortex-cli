import typer

from core.config import load_config
from core.loader import load_skills

app = typer.Typer(help="heart - CLI de skills e rules para apoiar o desenvolvimento (upstream e downstream).")


def main() -> None:
    load_config()
    load_skills(app)
    app()


if __name__ == "__main__":
    main()
