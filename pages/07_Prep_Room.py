# pages/07_Prep_Room.py
from __future__ import annotations
import streamlit as st

from ui import apply_theme, get_img_tag
from settings_io import load_settings
from storage import load_all
from view_filters import get_hidden, hide, reset
from keyer import ukey

PAGE_KEY = "prep_room"

st.set_page_config(page_title="Prep Room", page_icon="assets/prep_room.png", layout="wide")
cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()

c_ico, c_tit = st.columns([1, 15])
with c_ico:
    # Utilisation de get_img_tag pour bénéficier du "clip_circle" (coins blancs supprimés, mais intérieur intact)
    logo_html = get_img_tag("assets/prep_room.png", width="50px", clip_circle=True)
    st.markdown(logo_html, unsafe_allow_html=True)
with c_tit:
    st.title("Prep Room")

# --- données ---
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


# On n’affiche que les podiums non réalisés (done=False)
planning_todo = [p for p in planning_all if not p.get("done")]

# Masquage local spécifique à cette page (les “Send” ici ne suppriment pas globalement)
hidden_ids = get_hidden(PAGE_KEY)
planning = [p for p in planning_todo if p.get("category_id") not in hidden_ids]

# --- barre d’outils ---
t1, t2, t3 = st.columns([1, 1, 6])
with t1:
    if st.button("♻️ Show All", key=ukey(f"reset_{PAGE_KEY}"), use_container_width=True):
        reset(PAGE_KEY)
        st.rerun()
with t2:
    if st.button("🔄 Reload", key=ukey(f"reload_{PAGE_KEY}"), use_container_width=True):
        st.rerun()

st.divider()

if not planning:
    st.info("No podiums to prepare at the moment.")
else:
    st.caption("The next three podiums to prepare.")
    # On montre les 3 prochains uniquement
    subset = planning[:3]

    for i, it in enumerate(subset, start=1):
        pid = it.get("category_id")
        cat = cats.get(pid, {})
        title = cat.get("title") or pid or "—"
        meds = sorted(cat.get("medalists") or [], key=lambda m: int(m.get("rank", 99)))

        card = st.container()
        with card:
            c_head = st.columns([7, 2, 1, 2])
            c_head[0].markdown(f"### {i}. {title}")
            c_head[1].caption(f"`{pid}`")
            # Bouton Send -> masque localement pour cette page uniquement
            if c_head[3].button("✅ Send", key=ukey(f"val_{PAGE_KEY}_{pid}"), use_container_width=True):
                hide(PAGE_KEY, pid)
                st.rerun()

            st.write("— Medalists —")
            if meds:
                for m in meds:
                    medal = "🥇" if str(m.get("rank")) == "1" else ("🥈" if str(m.get("rank")) == "2" else "🥉")
                    right = m.get("club") if (cfg.show_club and m.get("club")) else m.get("nation", "")
                    right = f" `{right}`" if right else ""
                    st.markdown(f"{medal} **{m.get('name','—')}**{right}", unsafe_allow_html=True)
            else:
                st.caption("No medalists found.")

        st.divider()
