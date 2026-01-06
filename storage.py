from __future__ import annotations
# storage.py
import json, os, time, shutil
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _write_json(path: Path, value):
    """Écrit JSON de façon robuste sous Windows/OneDrive.
    1) écrit dans un .tmp unique
    2) tente os.replace()
    3) fallback: delete + move
    4) retries
    5) dernier recours: écriture directe (non atomique)
    """
    path = Path(path)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}_{int(time.time()*1000)}")

    # 1) écrire le JSON dans un .tmp
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) tenter le replace avec retries
    attempts = 6
    for i in range(attempts):
        try:
            os.replace(tmp, path)   # atomic move si possible
            return
        except PermissionError:
            # 3) fallback: supprimer l'ancien si présent puis move
            try:
                if path.exists():
                    # tenter une suppression (le lock OneDrive finit souvent par se libérer)
                    try:
                        os.remove(path)
                    except PermissionError:
                        pass
                shutil.move(str(tmp), str(path))
                return
            except PermissionError:
                # 4) attendre et réessayer
                time.sleep(0.25)

    # 5) dernier recours: écriture non atomique
    try:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

APP_ROOT = Path(__file__).parent.resolve()
DATA_DIR = (APP_ROOT / "data").resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

_FILES = {
    "vip":                      DATA_DIR / "vip.json",
    "categories":               DATA_DIR / "categories.json",
    "planning":                 DATA_DIR / "planning.json",
    "assignment":               DATA_DIR / "assignment.json",
    "final_block":              DATA_DIR / "final_block.json",
    "final_block_logo":         DATA_DIR / "final_block_logo.json",
    "final_block_jjif_logo":    DATA_DIR / "final_block_jjif_logo.json",
    "final_block_template":     DATA_DIR / "final_block_template.json",
    # 👇 nouveaux fichiers
    "finals_days":              DATA_DIR / "finals_days.json",       # { "1":[ids], "2":[ids], ... }
    "finals_days_meta":         DATA_DIR / "finals_days_meta.json",  # { "num_days": int }
}

_DEFAULTS: Dict[str, Any] = {
    "vip": [],
    "categories": [],
    "planning": [],
    "assignment": [],
    "final_block": {},            # dict attendu
    "final_block_logo": {},       # dict attendu
    "final_block_jjif_logo": {},  # dict attendu
    "final_block_template": {},   # dict attendu
    # 👇 nouveaux défauts
    "finals_days": {},            # mapping jour -> liste d'IDs de catégories
    "finals_days_meta": {"num_days": 1},
}

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return default
        return json.loads(text)
    except Exception:
        return default

def load(key: str) -> Any:
    path = _FILES.get(key)
    if not path:
        return None
    default = _DEFAULTS.get(key, None)
    return _read_json(path, default)

def save(key: str, value: Any) -> None:
    path = _FILES.get(key)
    if not path:
        raise KeyError(f"Unknown storage key: {key}")
    _write_json(path, value)

def load_all() -> Dict[str, Any]:
    from typing import Dict
    return {k: _read_json(p, _DEFAULTS.get(k, None)) for k, p in _FILES.items()}

def reset() -> None:
    for p in _FILES.values():
        if p.exists():
            p.unlink()

def data_dir() -> Path:
    return DATA_DIR

# ---------------------------
# Ecriture atomique (no-op locks)
# ---------------------------
_write_lock_flag = False

def begin_planning_write() -> None:
    global _write_lock_flag
    _write_lock_flag = True

def end_planning_write() -> None:
    global _write_lock_flag
    _write_lock_flag = False
