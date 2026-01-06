import json
from pathlib import Path
from typing import Dict, List, Set

FILE = Path(__file__).parent / "data" / "view_filters.json"
FILE.parent.mkdir(parents=True, exist_ok=True)

def _read() -> Dict[str, List[str]]:
    if FILE.exists():
        try:
            return json.loads(FILE.read_text(encoding="utf-8")) or {}
        except Exception:
            return {}
    return {}

def _write(data: Dict[str, List[str]]):
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_hidden(page_key: str) -> Set[str]:
    data = _read()
    return set(data.get(page_key, []))

def hide(page_key: str, category_id: str):
    data = _read()
    items = set(data.get(page_key, []))
    items.add(category_id)
    data[page_key] = sorted(items)
    _write(data)

def reset(page_key: str):
    data = _read()
    if page_key in data:
        data[page_key] = []
        _write(data)

def reset_all():
    """Réaffiche tous les podiums sur TOUTES les pages."""
    _write({})
