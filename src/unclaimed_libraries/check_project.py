"""
Анализатор сторонних библиотек Python-проекта.
- Автоматически определяет стандартные модули (sys.stdlib_module_names)
- Отсеивает все локальные модули/пакеты проекта
- Поддерживает namespace packages
- Параллельная обработка файлов
"""

import ast
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.metadata import packages_distributions
from os import PathLike
from pathlib import Path

from .constants import STD_LIB_MODULES

MAPPING = packages_distributions()


# ----------------------------------------------------------------------
# 2. Построение карты локальных модулей проекта
# ----------------------------------------------------------------------
def build_module_map(project_root: Path, exclude_dirs: set[str]) -> dict[str, Path]:
    """
    Создаёт словарь: имя модуля (точечная нотация) -> путь к файлу/папке.
    Включает:
      - все .py файлы как модули
      - папки с __init__.py как пакеты
      - папки без __init__.py, но содержащие .py (namespace packages)
    """
    module_map = {}
    root = project_root.resolve()

    # 1. Все .py файлы
    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        rel_path = py_file.relative_to(root).with_suffix("")
        module_name = ".".join(rel_path.parts)
        module_map[module_name] = py_file

        if py_file.name == "__init__.py":
            parent = ".".join(rel_path.parts[:-1])
            if parent:
                module_map[parent] = py_file.parent

    # 2. Папки как namespace packages (даже без __init__.py)
    for dir_path in root.rglob("*"):
        if dir_path.is_dir() and not any(part in exclude_dirs for part in dir_path.parts):
            rel = dir_path.relative_to(root)
            pkg_name = ".".join(rel.parts)
            if pkg_name not in module_map and any(dir_path.glob("*.py")):
                module_map[pkg_name] = dir_path

    # 3. Корневые .py файлы (кроме __init__.py)
    for py_file in root.glob("*.py"):
        if py_file.name != "__init__.py":
            module_map[py_file.stem] = py_file

    return module_map


def build_local_prefixes(module_map: dict[str, Path], project_root: Path) -> set[str]:
    """
    Строит множество всех возможных префиксов локальных модулей.
    Например, для модуля 'src.core.utils' добавит:
      'src.core.utils', 'src.core', 'src'
    Также добавляет все имена папок, содержащих .py файлы (для корректного распознавания пакетов).
    """
    prefixes = set()

    # Префиксы из ключей module_map
    for module_name in module_map:
        parts = module_name.split(".")
        for i in range(len(parts), 0, -1):
            prefixes.add(".".join(parts[:i]))

    # Дополнительно: все папки, которые являются родительскими для .py файлов
    # (помогает распознать импорт пакета, если папка не добавлена явно)
    for py_file in project_root.rglob("*.py"):
        rel_dir = py_file.relative_to(project_root).parent
        if str(rel_dir) != ".":
            pkg_name = ".".join(rel_dir.parts)
            prefixes.add(pkg_name)
            parts = pkg_name.split(".")
            for i in range(len(parts), 0, -1):
                prefixes.add(".".join(parts[:i]))

    return prefixes


# ----------------------------------------------------------------------
# 3. Извлечение импортов из одного файла (рефакторинг для снижения сложности)
# ----------------------------------------------------------------------
def _extract_import_aliases(node: ast.Import, libraries: set[str]) -> None:
    """Обрабатывает узел ast.Import."""
    for alias in node.names:
        # Принудительное преобразование в строку для удовлетворения типизатора
        lib_name = str(alias.name).split(".")[0]
        libraries.add(lib_name)


def _extract_import_from(node: ast.ImportFrom, libraries: set[str]) -> None:
    """Обрабатывает узел ast.ImportFrom."""
    if node.level > 0:  # относительный импорт – всегда локальный
        return
    if node.module:
        lib_name = str(node.module).split(".")[0]
        libraries.add(lib_name)


def _extract_dynamic_import(node: ast.Call, libraries: set[str]) -> None:
    """Обрабатывает динамические импорты (importlib.import_module, __import__)."""
    if (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
        and node.func.attr == "import_module"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ) or (
        isinstance(node.func, ast.Name)
        and node.func.id == "__import__"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ):
        lib_name = node.args[0].value.split(".")[0]  # type: ignore  # noqa: PGH003
        libraries.add(lib_name)  # type: ignore  # noqa: PGH003


def extract_imports_from_file(file_path: Path, local_prefixes: set[str]) -> set[str]:  # noqa: C901
    """
    Извлекает имена сторонних библиотек из одного .py файла.
    Относительные импорты и __future__ игнорируются.
    """
    libraries: set[str] = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return libraries

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            _extract_import_aliases(node, libraries)
        elif isinstance(node, ast.ImportFrom):
            _extract_import_from(node, libraries)
        elif isinstance(node, ast.Call):
            _extract_dynamic_import(node, libraries)

    # Фильтрация: убираем __future__, стандартные модули и локальные имена
    filtered = set()
    for lib in libraries:
        if lib == "__future__":
            continue
        if lib in STD_LIB_MODULES:
            continue
        if lib in local_prefixes:
            continue
        true_name = MAPPING.get(lib)
        if true_name:
            filtered.update(true_name)
    return filtered


def analyze_project_imports(
    project_path: str | PathLike,
    exclude_dirs: Iterable[str] | None,
    max_workers: int | None,
) -> set[str]:
    """
    Анализирует все .py файлы проекта и возвращает множество имён сторонних библиотек.
    :param project_path: путь к корню проекта
    :param exclude_dirs: дополнительные папки для исключения
    :param max_workers: количество потоков (по умолчанию число CPU)
    """
    root = Path(project_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"{root} не является директорией")

    default_exclude = {
        ".venv",
        "venv",
        "env",
        ".env",
        "__pycache__",
        "site-packages",
        "build",
        "dist",
        "docs",
        "examples",
    }
    if exclude_dirs:
        default_exclude.update(exclude_dirs)

    module_map = build_module_map(root, default_exclude)
    local_prefixes = build_local_prefixes(module_map, root)

    # Собираем все подлежащие анализу .py файлы
    py_files = []
    for py_file in root.rglob("*.py"):
        if any(part in default_exclude for part in py_file.parts):
            continue
        py_files.append(py_file)

    # Параллельная обработка
    all_libraries = set()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(extract_imports_from_file, py_file, local_prefixes): py_file
            for py_file in py_files
        }
        for future in as_completed(future_to_file):
            py_file = future_to_file[future]
            try:
                libs = future.result()
                all_libraries.update(libs)
            except Exception:  # noqa: BLE001, S110
                pass

    return all_libraries
