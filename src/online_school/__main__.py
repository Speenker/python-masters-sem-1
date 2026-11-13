"""Точка входа ``python -m online_school``."""

from __future__ import annotations

import sys

from online_school.cli import main

if __name__ == "__main__":
    sys.exit(main())
