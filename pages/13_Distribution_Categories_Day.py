# pages/13_Distribution_Categories_Day.py
from __future__ import annotations
from typing import Dict, Any, List
import streamlit as st

from ui import apply_theme, render_sidebar
from storage import load, save

st.set_page_config(page_title="Distribution Categories — Day", page_icon="🧩", layout="wide")
apply_theme()
render_sidebar()

st.title("🧩 Distribution Categories — Day")

# ---------- Data helpers ----------
def _load_categories() -> List[Dict[str, Any]]:
    """Loads categories from finals_categories (priority) or categories.
       Normalizes the 'title' field from name/Category/category if absent."""
    cats = load("finals_categories") or load("categories") or []
    norm = []
    for c in cats:
        if not isinstance(c, dict):
            continue
        cid = c.get("id") or c.get("cid")
        if not cid:
            continue
        title = c.get("title") or c.get("name") or c.get("Category") or c.get("category") or str(cid)
        cc = dict(c)
        cc["id"] = cid
        cc["title"] = title
        norm.append(cc)
    return norm

def _load_days_meta() -> int:
    meta = load("finals_days_meta") or {}
    return int(meta.get("num_days", 0) or 0)

def _save_days_meta(num_days: int):
    save("finals_days_meta", {"num_days": int(num_days)})

def _load_days_assign() -> Dict[str, List[str]]:
    """Map: '1' -> [category_id, ...]"""
    data = load("finals_days") or {}
    # sécurité : ne garder que des listes de strings
    safe = {}
    for k, v in data.items():
        if isinstance(v, list):
            safe[str(k)] = [str(x) for x in v]
    return safe

def _save_days_assign(mapping: Dict[str, List[str]]):
    save("finals_days", mapping)

# ---------- UI: param nombre de jours ----------
st.subheader("Settings")
cols = st.columns([2,2,6])
with cols[0]:
    num_days = st.number_input("Number of days", min_value=0, max_value=10,
                               value=_load_days_meta(), step=1,
                               help="0 = no distribution by day")
with cols[1]:
    if st.button("💾 Save", use_container_width=True):
        _save_days_meta(num_days)
        st.success("Number of days saved.")
        st.rerun()

# ---------- UI: liste des catégories + affectation ----------
cats = _load_categories()
days_map = _load_days_assign()

st.subheader("Category Assignment per Day")
if num_days <= 0:
    st.info("Set a number of days > 0 to enable distribution.")
else:
    # Choix du jour à éditer
    first_day = 1
    day_labels = [f"{i}" for i in range(first_day, num_days+1)]
    dcol1, dcol2 = st.columns([2, 6])
    with dcol1:
        sel_day = st.selectbox("🗓️ Day to edit", options=day_labels, index=0)

    # On construit une vue (liste) avec cases à cocher pour le jour choisi
    assigned_set = set(days_map.get(sel_day, []))
    st.caption("Check categories for the selected day.")
    selected_ids: List[str] = []
    for c in cats:
        cid = str(c["id"])
        checked = cid in assigned_set
        new_val = st.checkbox(c["title"], value=checked, key=f"chk_{sel_day}_{cid}")
        if new_val:
            selected_ids.append(cid)

    # Boutons d'action pour ce jour
    b1, b2, b3 = st.columns([2,2,6])
    with b1:
        if st.button("💾 Save this day", use_container_width=True):
            days_map[sel_day] = selected_ids
            _save_days_assign(days_map)
            st.success(f"Assignments for Day {sel_day} saved.")
            st.rerun()
    with b2:
        if st.button("🧹 Clear this day", use_container_width=True):
            days_map[sel_day] = []
            _save_days_assign(days_map)
            st.success(f"Day {sel_day} cleared.")
            st.rerun()

    st.divider()

    # ---------- Envoi vers Final Block ----------
    st.subheader("Send categories from this day to Final Block")
    st.caption("pushes ONLY categories from the selected day. They will arrive in 'To Assign' (unassigned).")
    if st.button("➡️ Push Day to Final Block", use_container_width=True):
        ids_for_day = days_map.get(sel_day, [])
        # construire payload finals (mat=0, order=0, assigned=False)
        finals_payload = []
        for cid in ids_for_day:
            finals_payload.append({
                "category_id": cid,
                "mat": 0,
                "order": 0,
                "assigned": False
            })

        # Conserver le nombre de tapis existant si déjà défini
        old_fb = load("final_block") or {}
        mats = int(old_fb.get("mats", 1))
        save("final_block", {
            "mats": mats if mats >= 1 else 1,
            "finals": finals_payload
        })
        st.success(f"{len(finals_payload)} category(ies) sent to Final Block (To Assign).")
        st.page_link("pages/11_Final_Block.py", label="Open Final Block", icon="🏁")
