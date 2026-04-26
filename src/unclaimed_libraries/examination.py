"""
Package Type Classifier
Определяет тип пакета (linter, framework, cli_tool, testing, static_analyzer, library, unknown)
на основе данных PyPI JSON API.
"""

import requests

from .constants import PYPI_URL, STATUS_OK


def get_pypi_metadata(package_name: str) -> dict | None:
    """Получает метаданные пакета из PyPI (требуется requests)."""

    url = PYPI_URL.format(package_name=package_name)
    try:
        resp = requests.get(url, timeout=40)
        if resp.status_code == STATUS_OK:
            return resp.json().get("info", {})
    except Exception:  # noqa: BLE001, S110
        pass
    return None


def classify_from_pypi(package_name: str) -> str:  # noqa: PLR0911
    """Классифицирует пакет по данным из PyPI (без установки)."""
    info = get_pypi_metadata(package_name)
    if not info:
        return "unknown"

    if package_name in {"stdlib-list", "unclaimed-libraries"} or "types" in package_name:
        return "types"

    classifiers = info.get("classifiers", [])

    for cls in classifiers:
        cls_lower = cls.lower()

        if "quality assurance" in cls_lower:
            return "linter"
        if "framework ::" in cls_lower:
            return "framework"
        if "testing" in cls_lower and "software development" in cls_lower:
            return "testing"
        if "static code analysis" in cls_lower or "type checking" in cls_lower:
            return "static_analyzer"
        if "console" in cls_lower or "terminal" in cls_lower:
            return "cli_tool"

    # Если нет специальных классификаторов – библиотека
    return "library"
