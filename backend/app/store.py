from __future__ import annotations

import json
import os
from pathlib import Path

from .models import AppState


def default_state() -> AppState:
    return AppState()


def load_state(path: Path) -> AppState:
    if not path.exists():
        state = default_state()
        save_state(path, state)
        return state
    data = json.loads(path.read_text(encoding="utf-8"))
    return AppState.model_validate(data)


def save_state(path: Path, state: AppState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    os.replace(tmp_path, path)
