# pages/08_Hotesse.py
from __future__ import annotations
from pathlib import Path
import base64
import streamlit as st

from settings_io import load_settings
from storage import load_all
from ui import apply_theme, get_img_tag

st.set_page_config(page_title="Hôtesse", page_icon="assets/hostess.png", layout="wide")

cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()

icon_html = get_img_tag("assets/hostess.png", width="40px", invert=False, clip_circle=True)
st.markdown(f"# {icon_html} Hôtesse", unsafe_allow_html=True)

APP_ROOT = Path(__file__).parents[1]
PHOTOS_DIR = APP_ROOT / "assets" / "photos"

data = load_all()
# --- lecture "planning" tolérante et triée (anti 'str'.get) ---
from storage import load_all

data = load_all()

raw_planning = data.get("planning") or []

# Si c'est un dict {id: item}, on convertit en liste
if isinstance(raw_planning, dict):
    raw_planning = list(raw_planning.values())

# On ne garde que les dicts (ignore les strings parasites)
safe_planning = [it for it in raw_planning if isinstance(it, dict)]

# Tri sécurisé
def _ord(v):
    try:
        return int((v or {}).get("order", 0))
    except Exception:
        return 0

planning = sorted(safe_planning, key=_ord)
cats = { (c.get("id") or c.get("title")): c for c in (data.get("categories") or []) }
assign = { a.get("category_id"): a.get("vip_ids", []) for a in (data.get("assignment") or []) }
vips   = { v.get("id"): v for v in (data.get("vip") or []) }

if "hotesse_idx" not in st.session_state:
    st.session_state.hotesse_idx = 0

# clamp
if planning:
    st.session_state.hotesse_idx = max(0, min(st.session_state.hotesse_idx, len(planning)-1))

def resolve_photo_path(vip: dict) -> Path | None:
    p = str(vip.get("photo") or "").strip()
    if p:
        cand = Path(p)
        if not cand.is_absolute():
            cand = APP_ROOT / p
        if cand.exists():
            return cand
    vid = str(vip.get("id") or "").strip()
    for ext in (".png", ".jpg", ".jpeg"):
        cand = PHOTOS_DIR / f"{vid}{ext}"
        if cand.exists():
            return cand
    return None

def file_to_data_uri(path: Path) -> str | None:
    try:
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None

AV = 110  # taille vignette

def vip_card_html(v: dict) -> str:
    name = v.get("name", v.get("id",""))
    role = (v.get("role") or "").strip()
    if cfg.hostess_show_photos:
        p = resolve_photo_path(v)
        if p and p.exists():
            uri = file_to_data_uri(p)
            if uri:
                img = f'<img src="{uri}" alt="{name}" style="width:{AV}px;height:{AV}px;border-radius:12px;object-fit:cover;object-position:center;margin-bottom:6px;">'
            else:
                img = f'<div class="jj-avatar" style="width:{AV}px;height:{AV}px;border-radius:12px;background:#1C2B4A;color:#FFD700;display:flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:6px;">{(name[:2] or "?").upper()}</div>'
        else:
            img = f'<div class="jj-avatar" style="width:{AV}px;height:{AV}px;border-radius:12px;background:#1C2B4A;color:#FFD700;display:flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:6px;">{(name[:2] or "?").upper()}</div>'
    else:
        img = f'<div class="jj-avatar" style="width:{AV}px;height:{AV}px;border-radius:12px;background:#1C2B4A;color:#FFD700;display:flex;align-items:center;justify-content:center;font-weight:700;margin-bottom:6px;">{(name[:2] or "?").upper()}</div>'

    cap = f"<b>{name}</b>" + (f"<br><small><i>{role}</i></small>" if role else "")
    return f'<div class="jj-card" style="padding:8px;">{img}<div class="jj-caption">{cap}</div></div>'

def render_current(idx: int):
    if not planning:
        st.info("No categories in planning.")
        return

    cur = planning[idx]
    cid = cur.get("category_id")
    cat = cats.get(cid, {})
    title = cat.get("title") or cid or "—"

    # Entête + navigation
    left, center, right = st.columns([1,2,1])
    with left:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(idx == 0)):
            st.session_state.hotesse_idx = idx - 1
            st.rerun()
    with center:
        st.markdown(f"<h2 style='text-align:center;'>{title}</h2>", unsafe_allow_html=True)
        st.caption(f"Category {idx+1} / {len(planning)}")
    with right:
        if st.button("Next ➡️", use_container_width=True, disabled=(idx >= len(planning)-1)):
            st.session_state.hotesse_idx = idx + 1
            st.rerun()

    # VIP assignés
    vids = assign.get(cid, [])
    if not vids:
        st.info("No VIP assigned.")
        return

    # Fetch roles
    assign_obj = next((a for a in (data.get("assignment") or []) if a.get("category_id") == cid), {})
    roles_map = assign_obj.get("vip_roles") or {}

    cards = []
    for vid in vids:
        v = vips.get(vid, {}).copy() # copy to not mutate global state
        
        # Inject medal role into the 'role' field for display, or prepend it
        medal_role = roles_map.get(vid)
        if medal_role and medal_role != "General":
            # Prepend to existing role or set as role
            current_role = v.get("role") or ""
            icon = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}.get(medal_role, "")
            v["role"] = f"{icon} {medal_role} — {current_role}" if current_role else f"{icon} {medal_role}"
            
        cards.append(vip_card_html(v))

    st.markdown('<div class="jj-grid" style="--card-min:160px;">' + "".join(cards) + "</div>", unsafe_allow_html=True)

# Rendu principal
render_current(st.session_state.hotesse_idx)
