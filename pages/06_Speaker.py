# pages/06_Speaker.py
import streamlit as st
from ui import apply_theme, render_sidebar
from settings_io import load_settings
from storage import load_all

st.set_page_config(page_title="Speaker", page_icon="🎤", layout="wide")

# Thème + sidebar
cfg = load_settings()
apply_theme()
render_sidebar()

st.title("🎤 Speaker")

# Chargement des données persistées
data = load_all()
categories = data.get("categories") or []           # liste de dicts: {id, title, medalists: [...]}
assignments_list = data.get("assignment") or []
assignments = {a.get("category_id"): a.get("vip_ids") for a in assignments_list if isinstance(a, dict)}
vip_list = data.get("vip") or []                    # [{id, name, ioc, function, photo_path, ...}]

# Index courant en session (navigation une seule catégorie à la fois)
if "speaker_idx" not in st.session_state:
    st.session_state["speaker_idx"] = 0

# Construire une liste ordonnée de catégories à afficher
# - si un "planning" existe et non vide => respecter cet ordre
# - sinon, on prend l’ordre tel que dans categories
planning = data.get("planning") or []
if planning:
    # planning peut être une simple liste d'ids
    ordered_ids = [p if isinstance(p, str) else p.get("id") for p in planning]
    ordered = [c for cid in ordered_ids for c in categories if (c.get("id") == cid or c.get("title") == cid)]
    # fallback si certains IDs ne matchent pas
    if not ordered:
        ordered = categories[:]
else:
    ordered = categories[:]

total = len(ordered)

if total == 0:
    st.warning("No categories to display. Import results and/or set a planning.")
    st.stop()

# Sécuriser l’index
st.session_state["speaker_idx"] = max(0, min(st.session_state["speaker_idx"], total - 1))
cur = ordered[st.session_state["speaker_idx"]]
cid = cur.get("id") or cur.get("title") or f"cat_{st.session_state['speaker_idx']}"
title = cur.get("title", "Unnamed Category")

# Barre de navigation
nav_l, nav_c, nav_r = st.columns([1, 6, 1])
with nav_l:
    if st.button("⬅️ Previous", use_container_width=True, disabled=(st.session_state["speaker_idx"] <= 0)):
        st.session_state["speaker_idx"] -= 1
with nav_r:
    if st.button("Next ➡️", use_container_width=True, disabled=(st.session_state["speaker_idx"] >= total - 1)):
        st.session_state["speaker_idx"] += 1

# En-tête catégorie
# Option d’affichage club/IOC depuis Settings (si présent)
show_club = getattr(cfg, "show_club_names", False)

def fmt_athlete(m: dict) -> str:
    """Rend un affichage lisible pour un médaillé."""
    # attendu depuis l’import: {'rank': 1..3, 'name': '...', 'club': '...', 'ioc': 'FRA'}
    rank = m.get("rank")
    name = m.get("name") or "N/A"
    club = m.get("club")
    ioc = (m.get("ioc") or "").upper().strip()

    # Affichage IOC/club selon param
    right = ""
    if show_club and club:
        right = f" — {club}"
    elif ioc:
        right = f" — {ioc}"

    # Emoji médaille
    medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(int(rank) if str(rank).isdigit() else None, "🏅")
    return f"{medal} **{name}**{right}"

# construire un dict id -> vip
vip_by_id = {v.get("id") or v.get("name"): v for v in vip_list}

# Helper rendering functions
def render_category_block(idx, is_next=False):
    if idx >= total:
        if is_next:
            st.markdown("### 🏁 End of Ceremony")
            st.caption("No more categories.")
        return

    obj = ordered[idx]
    c_id = obj.get("id") or obj.get("title") or "Unknown"
    c_title = obj.get("title", "Unnamed Category")
    
    # Header
    prefix = "⏭️ Next: " if is_next else "Now: "
    st.markdown(f"### {prefix}{c_title}")
    
    # Medalists
    meds = obj.get("medalists") or []
    if not meds:
        st.caption("No medalists.")
    else:
        # Sort desc
        def _rk(x):
            try: return int(x.get("rank"))
            except: return 999
        meds = sorted(meds, key=_rk, reverse=True)
        
        for m in meds:
            st.markdown(f"{fmt_athlete(m)}")

    # VIPs
    st.markdown("---")
    st.caption("**Presentation**")
    
    # Get assignments
    # We need to find assignment object for this Category ID
    a_obj = next((a for a in assignments_list if isinstance(a, dict) and a.get("category_id") == c_id), {})
    v_ids = a_obj.get("vip_ids") or []
    r_map = a_obj.get("vip_roles") or {}
    
    if not v_ids:
        st.caption("(No VIP assigned)")
    else:
        # Sort VIPs
        def _vip_order(vid):
            r = r_map.get(vid)
            if r == "Bronze": return 1
            if r == "Silver": return 2
            if r == "Gold":   return 3
            return 4
        
        sorted_vids = sorted(v_ids, key=_vip_order)
        
        for vid in sorted_vids:
            v = vip_by_id.get(vid) or {}
            vname = v.get("name") or vid
            # Fix: The attribute in VIP data is 'role', not 'function'
            vfun = v.get("role") or ""
            role = r_map.get(vid)
            
            icon = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}.get(role, "•") if (role and role!="General") else "•"
            
            line = f"{icon} **{vname}**"
            if vfun: 
                line += f" — {vfun}"
            st.markdown(line)

# Layout: Vertical (Present then Next)

# Present
st.info("Present")
render_category_block(st.session_state["speaker_idx"], is_next=False)

st.markdown("---")
if st.button("✅ Done / Next Category", use_container_width=True, key="done_btn"):
    if st.session_state["speaker_idx"] < total - 1:
        st.session_state["speaker_idx"] += 1
        st.rerun()

st.divider()

# Next
st.success("Next")
render_category_block(st.session_state["speaker_idx"] + 1, is_next=True)

st.divider()
st.caption(f"Category {st.session_state['speaker_idx']+1}/{total} — id: `{cid}`")
