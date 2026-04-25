import sys

STD_LIB_MODULES = set(sys.stdlib_module_names)

DEFAULT_EXCLUDE = {
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
    "migrations",
}

PYPI_URL = """https://pypi.org/pypi/{package_name}/json"""
STATUS_OK = 200
ASSISTANTS = {"static_analyzer", "cli_tool", "linter", "unknown", "types"}
