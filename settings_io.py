# settings_io.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict

APP_ROOT = Path(__file__).parent
DATA_DIR = APP_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_PATH = DATA_DIR / "settings.json"


@dataclass
class Settings:
    # --- seules les clés ci-dessous sont autorisées ---
    cycle_seconds: int = 10
    speaker_large_font: bool = False
    
    # Global / Competition
    competition_name: str = ""
    competition_country: str = ""
    competition_city: str = ""
    date_from: str = ""
    date_to: str = ""
    event_logo: str = ""
    federation_logo: str = ""
    
    # Display Options
    show_club: bool = False   # Legacy key? Check usage. 
    show_clubs: bool = True   # Key used in 00_Settings.py
    vip_show_photos: bool = True
    hostess_show_photos: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -------------------- utilitaires I/O --------------------

def _read_json_safe(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# -------------------- sanitation & coercion --------------------

_ALLOWED_KEYS = set(Settings.__annotations__.keys())

def _filter_allowed_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    """Supprime toute clé inconnue (ex: 'theme') pour éviter Settings(**d) -> TypeError."""
    return {k: v for k, v in (d or {}).items() if k in _ALLOWED_KEYS}

def _to_bool(v: Any, default: bool = False) -> bool:
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return bool(v)
    if isinstance(v, str): return v.strip().lower() in ("1", "true", "yes", "on")
    return default

def _coerce_types(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Ne touche qu'aux clés autorisées; ignore silencieusement le reste."""
    r = _filter_allowed_keys(raw)  # <-- filtre d'abord !
    out: Dict[str, Any] = {}

    # ints
    try:
        out["cycle_seconds"] = int(r.get("cycle_seconds", 10))
    except Exception:
        out["cycle_seconds"] = 10

    # strings
    out["competition_name"]    = str(r.get("competition_name", ""))
    out["competition_country"] = str(r.get("competition_country", ""))
    out["competition_city"]    = str(r.get("competition_city", ""))
    out["date_from"]           = str(r.get("date_from", ""))
    out["date_to"]             = str(r.get("date_to", ""))
    out["event_logo"]          = str(r.get("event_logo", ""))
    out["federation_logo"]     = str(r.get("federation_logo", ""))

    # bools
    out["speaker_large_font"]  = _to_bool(r.get("speaker_large_font",  False))
    out["show_club"]           = _to_bool(r.get("show_club",           False))
    out["show_clubs"]          = _to_bool(r.get("show_clubs",          True)) # Add this
    out["vip_show_photos"]     = _to_bool(r.get("vip_show_photos",     True))
    out["hostess_show_photos"] = _to_bool(r.get("hostess_show_photos", True))

    return out

def _merge_with_defaults(raw: Dict[str, Any]) -> Settings:
    # On filtre AVANT, on convertit, puis on refiltre par sécurité
    coerced = _coerce_types(_filter_allowed_keys(raw))
    coerced = _filter_allowed_keys(coerced)
    defaults = Settings().to_dict()
    merged = {**defaults, **coerced}
    return Settings(**merged)


# -------------------- API publique --------------------

def load_settings() -> Settings:
    raw = _read_json_safe(SETTINGS_PATH)
    return _merge_with_defaults(raw)

def save_settings(patch: Dict[str, Any]) -> Settings:
    current = _read_json_safe(SETTINGS_PATH)

    # fusionne, filtre, convertit, fusionne avec défauts
    combined = {**current, **(patch or {})}
    combined = _filter_allowed_keys(combined)          # <-- filtre dès maintenant
    final_obj = _merge_with_defaults(combined)

    # on n’écrit QUE les clés autorisées
    _atomic_write_json(SETTINGS_PATH, final_obj.to_dict())
    return final_obj


# -------------------- helpers --------------------

def settings_path() -> Path:
    return SETTINGS_PATH

def ensure_defaults() -> Settings:
    s = load_settings()
    try:
        if not SETTINGS_PATH.exists():
            _atomic_write_json(SETTINGS_PATH, s.to_dict())
    except Exception:
        pass
    return s
