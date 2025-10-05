#!/usr/bin/env python3
"""Generate Pipfile from pyproject.toml for Vercel deployment."""

import tomllib
from pathlib import Path


def generate_pipfile():
    """Generate Pipfile from pyproject.toml dependencies."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    pipfile_path = project_root / "Pipfile"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    dependencies = data["project"]["dependencies"]
    python_version = data["project"]["requires-python"].replace(">=", "")

    pipfile_content = """[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
"""

    for dep in dependencies:
        if "[" in dep:  # Handle extras like strawberry-graphql[django]
            name, version_part = dep.split("[", 1)
            extra, version_part = version_part.split("]", 1)
            version = version_part or "*"
            pipfile_content += f'{name} = {{extras = ["{extra}"], version = "{version}"}}\n'
        else:
            if ">=" in dep:
                name, version = dep.split(">=", 1)
                version = f">={version}"
            else:
                name = dep
                version = "*"
            pipfile_content += f'{name} = "{version}"\n'

    pipfile_content += f"""
[dev-packages]

[requires]
python_version = "{python_version}"
"""

    with open(pipfile_path, "w") as f:
        f.write(pipfile_content)

    print(f"Generated {pipfile_path} from {pyproject_path}")


if __name__ == "__main__":
    generate_pipfile()
