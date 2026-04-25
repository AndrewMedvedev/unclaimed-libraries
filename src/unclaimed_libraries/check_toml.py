import re
import tomllib


def extract_name(dep: str) -> str:
    """
    Убирает версии, extras и environment markers:
    requests[socks]>=2.0; python_version > "3.8"
    → requests
    """
    # убрать environment markers
    dep = dep.split(";", maxsplit=1)[0]

    # убрать extras
    dep = dep.split("[")[0]

    # убрать версии
    dep = re.split(r"[<>=!~]", dep)[0]

    return dep.strip()


def get_dependency_names() -> set:
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    deps = set()

    # --- PEP 621 (uv и др.) ---
    project = data.get("project", {})

    for dep in project.get("dependencies", []):
        deps.add(extract_name(dep))

    # --- Poetry ---
    poetry = data.get("tool", {}).get("poetry", {})

    for name in poetry.get("dependencies", {}):
        if name.lower() != "python":
            deps.add(name)

    # dev (новый формат)
    for group in poetry.get("group", {}).values():
        deps.update(group.get("dependencies", {}).keys())

    # dev (старый формат)
    deps.update(poetry.get("dev-dependencies", {}).keys())

    return deps
