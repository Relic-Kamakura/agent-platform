from __future__ import annotations

import os
import pathlib

CHAPTER_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = CHAPTER_DIR.parent
APP_DIR = pathlib.Path(os.environ.get("AGENT_APP_DIR", REPO_ROOT / "07-full-app"))
