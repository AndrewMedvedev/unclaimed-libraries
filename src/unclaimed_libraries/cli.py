import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .app import unclaimed_libraries

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Поиск неиспользуемых зависимостей в проекте",
    )

    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        type=Path,
        help="Путь к проекту (по умолчанию: текущая папка)",
    )

    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Список директорий для исключения",
    )

    return parser.parse_args()


def print_result(result: list[str]) -> None:

    if not result:
        console.print("[green]✅ No unused dependencies found[/green]")
        return

    table = Table(title="❌ Unused dependencies")

    table.add_column("№", style="dim", width=4)
    table.add_column("lib", style="red")

    for i, lib in enumerate(result, start=1):
        table.add_row(str(i), lib)

    console.print(table)


def main() -> int:
    args = parse_args()

    try:
        with console.status("[cyan]Project analysis...[/cyan]"):
            result = unclaimed_libraries(
                project_path=args.project_path.resolve(),
                exclude_dirs=args.exclude or [],
            )
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Error while analyzing the project:[/red] {e}")
        return 2

    return 1 if result else 0


if __name__ == "__main__":
    raise SystemExit(main())
