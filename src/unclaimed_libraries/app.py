from collections.abc import Iterable
from os import PathLike

from .check_project import analyze_project_imports
from .check_toml import get_dependency_names
from .constants import ASSISTANTS
from .examination import classify_from_pypi


def unclaimed_libraries(
    project_path: str | PathLike = ".",
    exclude_dirs: Iterable[str] | None = None,
    max_workers: int | None = None,
) -> list[str]:
    depends = get_dependency_names()
    imports = analyze_project_imports(project_path, exclude_dirs, max_workers)
    unused = depends & imports
    result: list = []
    for i in unused:
        library_type = classify_from_pypi(i)
        if library_type in ASSISTANTS:
            continue
        result.append(i)
    return result
