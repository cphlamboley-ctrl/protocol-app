# pages/05_Live.py
from __future__ import annotations
import streamlit as st

from ui import apply_theme
from settings_io import load_settings
from storage import load_all
from view_filters import get_hidden, hide, reset
from keyer import ukey

PAGE_KEY = "live"

st.set_page_config(page_title="Live", page_icon="🎬", layout="wide")
cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()

st.title("🎬 Live")

data = load_all()
cats = {(c.get("id") or c.get("title")): c for c in (data.get("categories") or [])}
# --- lecture "planning" tolérante et triée ---
raw_planning = data.get("planning") or []

# Si jamais on a un dict {id: item}, on le convertit en liste
if isinstance(raw_planning, dict):
    raw_planning = list(raw_planning.values())

# On ne garde que les objets dict valides
safe_planning = [it for it in raw_planning if isinstance(it, dict)]

# Tri sécurisé (order peut être string ou absent)
def _ord(v):
    try:
        return int((v or {}).get("order", 0))
    except Exception:
        return 0

planning_all = sorted(safe_planning, key=_ord)

hidden_ids = get_hidden(PAGE_KEY)
planning = [p for p in planning_all if p.get("category_id") not in hidden_ids]

# barre d’outils
t1, t2, t3, t4 = st.columns([1, 1, 4, 1])
with t1:
    if st.button("♻️ Show All", key=ukey(f"reset_{PAGE_KEY}"), use_container_width=True):
        reset(PAGE_KEY); st.rerun()
with t2:
    if st.button("🔄 Reload", key=ukey(f"reload_{PAGE_KEY}"), use_container_width=True):
        st.rerun()
with t4:
    st.caption(f"Planning: {len(planning_all)}")

st.divider()

def section(idx: int, label: str):
    if idx >= len(planning):
        return None, None
    pid = planning[idx]["category_id"]
    cat = cats.get(pid, {})
    st.subheader(f"{label} — {pid} : {cat.get('title', '—')}")
    meds = cat.get("medalists") or []
    for m in sorted(meds, key=lambda x: int(x.get("rank", 99))):
        medal = "🥇" if str(m.get("rank")) == "1" else ("🥈" if str(m.get("rank")) == "2" else "🥉")
        right = m.get("club") if (cfg.show_club and m.get("club")) else m.get("nation", "")
        right = f" &nbsp;&nbsp; `{right}`" if right else ""
        st.markdown(f"{medal} **{m.get('name','—')}**{right}", unsafe_allow_html=True)
    st.divider()
    return pid, cat.get("title")

cur = section(0, "Current")
nxt = section(1, "Next")
aft = section(2, "After")

if cur and cur[0]:
    if st.button("✅ Validate here", key=ukey(f"val_{PAGE_KEY}_{cur[0]}"), use_container_width=True):
        hide(PAGE_KEY, cur[0]); st.rerun()
else:
    st.info("No category to display at the moment.")
