
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any

API_CFG_PATH = Path(__file__).parent / "data" / "api_config.json"
API_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class ApiConfig:
    base_url: str = "http://localhost:8000"
    event_id: str = ""
    api_key: str = ""
    timeout_sec: int = 8
    refresh_sec: int = 10
    auto_cycle: bool = True
    extra_headers: Dict[str, str] | None = None

def _merge(defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
    out = defaults.copy()
    for k, v in (loaded or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict): out[k].update(v)
        else: out[k]=v
    return out

def load_api() -> ApiConfig:
    cfg = ApiConfig()
    if API_CFG_PATH.exists():
        try:
            raw = json.loads(API_CFG_PATH.read_text(encoding="utf-8"))
            cfg = ApiConfig(**_merge(asdict(cfg), raw))
        except Exception:
            pass
    return cfg

def save_api(new_values: Dict[str, Any]) -> ApiConfig:
    cfg = load_api()
    merged = _merge(asdict(cfg), new_values or {})
    API_CFG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return ApiConfig(**merged)

def reset_api() -> ApiConfig:
    defaults = ApiConfig()
    API_CFG_PATH.write_text(json.dumps(asdict(defaults), ensure_ascii=False, indent=2), encoding="utf-8")
    return defaults
