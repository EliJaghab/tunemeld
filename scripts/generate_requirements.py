#!/usr/bin/env python3
"""
Generate requirements.txt from pyproject.toml for Vercel deployment.
Only includes core dependencies, excludes ETL dependencies.
"""

import tomllib
from pathlib import Path


def generate_requirements():
    """Generate requirements.txt from pyproject.toml core dependencies."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    requirements_path = project_root / "requirements.txt"

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found")
        return

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    dependencies = data.get("project", {}).get("dependencies", [])

    if not dependencies:
        print("ERROR: No dependencies found in pyproject.toml")
        return

    # Write core dependencies only (exclude ETL extras)
    with open(requirements_path, "w") as f:
        for dep in sorted(dependencies):
            f.write(f"{dep}\n")

    print(f"Generated requirements.txt with {len(dependencies)} core dependencies")


if __name__ == "__main__":
    generate_requirements()
