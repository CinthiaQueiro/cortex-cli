import importlib.util
from pathlib import Path

import typer
import yaml

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def load_skills(app: typer.Typer) -> None:
    if not SKILLS_DIR.is_dir():
        return

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        manifest_path = skill_dir / "manifest.yaml"
        if not manifest_path.is_file():
            continue

        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        name = manifest["name"]
        description = manifest.get("description", "")

        module = _load_module(skill_dir / "skill.py", module_name=f"heart_skill_{skill_dir.name}")
        run_fn = getattr(module, "run")

        app.command(name=name, help=description)(run_fn)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
