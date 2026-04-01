#!/usr/bin/env python3
"""ИИ-агент для открытия сайта RBC в Safari (или браузере по умолчанию)."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import webbrowser
from dataclasses import dataclass


@dataclass
class SafariAgent:
    """Агент, который открывает сайт RBC."""

    url: str = "https://www.rbc.ru"

    def run(self) -> str:
        system = platform.system()

        if system == "Darwin":
            self._open_in_safari()
            return "Safari"

        self._open_in_default_browser()
        return "default"

    def _open_in_safari(self) -> None:
        applescript = f'''
        tell application "Safari"
            activate
            open location "{self.url}"
        end tell
        '''
        subprocess.run(["osascript", "-e", applescript], check=True)

    def _open_in_default_browser(self) -> None:
        opened = webbrowser.open(self.url, new=2)
        if not opened:
            print(
                "Предупреждение: браузер не удалось открыть автоматически; "
                f"откройте вручную: {self.url}"
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://www.rbc.ru", help="URL для открытия")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    agent = SafariAgent(url=args.url)

    try:
        browser_name = agent.run()
        if browser_name == "Safari":
            print(f"Готово: Safari открыл сайт {agent.url}")
        else:
            print(f"Safari недоступен. Открыл сайт {agent.url} в браузере по умолчанию")
        return 0
    except Exception as error:  # noqa: BLE001
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
