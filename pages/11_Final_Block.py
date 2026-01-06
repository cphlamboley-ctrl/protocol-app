# pages/11_Final_Block.py
from __future__ import annotations
from typing import List, Dict, Any
import uuid
import streamlit as st

from ui import apply_theme, render_sidebar, get_img_tag
from settings_io import load_settings
from storage import load, save

# ---------- Page config + thème + sidebar ----------
st.set_page_config(page_title="Final Block", page_icon="assets/final_block.png", layout="wide")
apply_theme()
render_sidebar()

icon_html = get_img_tag("assets/final_block.png", width="40px", invert=True)
st.markdown(f"# {icon_html} Final Block", unsafe_allow_html=True)

EXPORT_PAGE_PATH = "pages/12_Final_Block_Export.py"

# ---------- helpers ----------
def _load_fb() -> Dict[str, Any]:
    """Charge le final_block en imposant les imports à 'À assigner' (mat=0, order=0, assigned=False)."""
    fb = load("final_block") or {}
    mats = int(fb.get("mats") or 1)
    finals = fb.get("finals") or []  # [{"category_id","order","mat"} ou breaks]
    changed = False

    for i, f in enumerate(finals):
        # normalise les breaks
        if f.get("is_break"):
            # CORRECTION BUG: Si mat=0 ("To Assign"), `0 or 1` donnait 1.
            # Il faut accepter 0.
            current_mat = f.get("mat")
            if current_mat is None:
                current_mat = 1 # Default si null
            f["mat"] = int(current_mat)
            
            f["order"] = int(f.get("order") or (i + 1))
            f.setdefault("id", f.get("id") or f.get("category_id") or f"__BREAK__:{uuid.uuid4().hex[:8]}")
            continue

        # Catégorie
        # Toute importation doit démarrer en 'non affectée' (sauf déjà assignée)
        m_raw = f.get("mat", 0)
        try:
            m = int(m_raw)
        except Exception:
            m = 0

        if not f.get("assigned"):
            # Forcer à "à assigner"
            if m != 0 or f.get("order"):
                changed = True
            f["mat"] = 0
            f["order"] = 0
            f["assigned"] = False
        else:
            # Si déjà assignée, clamp bornes
            if m < 0 or m > mats:
                f["mat"] = 0
                f["order"] = 0
                f["assigned"] = False
                changed = True

    if changed:
        save("final_block", {"mats": max(1, mats), "finals": finals})
    return {"mats": max(1, mats), "finals": finals}

def _save_fb(mats: int, finals: List[Dict[str, Any]]):
    save("final_block", {"mats": int(mats), "finals": finals})

def _cats_by_id() -> Dict[str, Dict[str, Any]]:
    """Map ID -> catégorie normalisée (toujours une clé 'title')."""
    cats = load("finals_categories") or load("categories") or []
    by_id = {}
    for c in cats:
        if not isinstance(c, dict):
            continue
        cid = c.get("id") or c.get("cid")
        if not cid:
            continue
        title = c.get("title") or c.get("name") or c.get("Category") or c.get("category") or str(cid)
        cc = dict(c)
        cc["title"] = title
        by_id[cid] = cc
    return by_id

def _mat_items(finals: List[Dict[str, Any]], mat: int) -> List[Dict[str, Any]]:
    return sorted([f for f in finals if int(f.get("mat", 0)) == mat],
                  key=lambda x: x.get("order", 999999))

def _reindex_orders_by_mat(finals: List[Dict[str, Any]], mats: int):
    for m in range(1, mats + 1):
        items = [f for f in finals if int(f.get("mat", 0)) == m]
        items = sorted(items, key=lambda x: x.get("order", 999999))
        for idx, f in enumerate(items, start=1):
            f["order"] = idx

def _swap_up(finals: List[Dict[str, Any]], mat: int, idx_in_mat: int):
    items = _mat_items(finals, mat)
    if not (0 < idx_in_mat < len(items)): 
        return
    a, b = items[idx_in_mat - 1], items[idx_in_mat]
    a["order"], b["order"] = b["order"], a["order"]

def _swap_down(finals: List[Dict[str, Any]], mat: int, idx_in_mat: int):
    items = _mat_items(finals, mat)
    if not (0 <= idx_in_mat < len(items) - 1): 
        return
    a, b = items[idx_in_mat], items[idx_in_mat + 1]
    a["order"], b["order"] = b["order"], a["order"]

def _move_top(finals: List[Dict[str, Any]], mat: int, idx_in_mat: int):
    items = _mat_items(finals, mat)
    if not (0 <= idx_in_mat < len(items)): 
        return
    items[idx_in_mat]["order"] = 0
    _reindex_orders_by_mat(finals, mats)

def _add_break(finals: List[Dict[str, Any]], mat: int):
    items = _mat_items(finals, mat)
    next_order = (items[-1]["order"] + 1) if items else 1
    finals.append({
        "id": f"__BREAK__:{uuid.uuid4().hex[:8]}",
        "is_break": True,
        "mat": mat,
        "order": next_order
    })

def _delete_break(finals: List[Dict[str, Any]], break_id: str):
    idx = next((i for i, it in enumerate(finals) if it.get("is_break") and it.get("id") == break_id), None)
    if idx is not None:
        finals.pop(idx)

def _go_export(mode: str, mats: int, finals: List[Dict[str, Any]], day_label: str):
    _save_fb(mats, finals)
    st.session_state["final_block_export_mode"] = mode
    st.session_state["final_block_export_day"] = day_label
    try:
        st.switch_page("pages/12_Final_Block_Export.py")
    except Exception:
        st.page_link("pages/12_Final_Block_Export.py", label="➡️ Export page", icon="🧾")


def _load_days_meta() -> int:
    meta = load("finals_days_meta") or {}
    return int(meta.get("num_days", 0) or 0)

def _load_days_assign() -> Dict[str, list]:
    return load("finals_days") or {}

def _filter_by_day(finals: List[Dict[str, Any]], day_key: str | None, days_map: Dict[str, list]) -> List[Dict[str, Any]]:
    if not day_key or day_key == "ALL":
        return finals
    ids = set(days_map.get(day_key, []))
    if not ids:
        return [f for f in finals if f.get("is_break")]
    return [f for f in finals if f.get("is_break") or f.get("category_id") in ids]

# ---------- data ----------
cfg = load_settings()
fb = _load_fb()
mats = fb["mats"]
finals = fb["finals"]
cats_map = _cats_by_id()
if not finals:
    st.info("No finals set. Push a day to Final Block from “Distribution Categories — Day”.")
    st.stop()

# ---------- styles ----------
st.markdown("""
<style>
.btn, .btn-icon, .btn-header {height:0; padding:0; margin:0;}
.btn ~ div.stButton > button,
.btn + div.stButton > button,
.btn-header ~ div.stButton > button,
.btn-header + div.stButton > button{
  background:#2563EB !important; color:#fff !important;
  padding:.24rem .55rem !important; min-height:30px !important; border-radius:8px !important; font-size:.90rem !important;
}
.btn-icon ~ div.stButton > button,
.btn-icon + div.stButton > button{
  background:#2563EB !important; color:#fff !important;
  padding:.22rem .5rem !important; min-height:28px !important; border-radius:8px !important; font-size:.85rem !important;
}

/* --- Spécifique : bouton ↩︎ à assigner --- */
.unassign ~ div.stButton > button {
  background:#2563EB !important; color:#fff !important; border:none !important;
}
div.stButton > button:disabled {
  background-color:#1e293b !important; color:#94a3b8 !important; border:none !important;
}

.final-card{
  border:1px solid #334155; border-radius:10px; padding:.45rem .6rem; margin-bottom:.4rem;
  min-height:56px; display:flex; align-items:center; justify-content:space-between;
  background:rgba(30,41,59,.30);
}
.final-title{ font-weight:600; }
.break-card{
  border:1px dashed #334155; border-radius:10px; padding:.45rem .6rem; margin-bottom:.4rem;
  min-height:46px; display:flex; align-items:center; justify-content:space-between;
  background:rgba(30,41,59,.18);
  font-style:italic;
}
</style>
""", unsafe_allow_html=True)

# ---------- filtre par jour ----------
num_days = _load_days_meta()
days_map = _load_days_assign()
day_options = ["ALL"] + [f"{i}" for i in range(1, max(1, num_days) + 1)] if num_days > 0 else ["ALL"]
col_day, _ = st.columns([2, 5])
with col_day:
    sel_day_label = st.selectbox("🗓️ Day filter", options=day_options, index=0,
                                 help="Filters category display by day (from Distribution).")

visible_finals = _filter_by_day(finals, None if sel_day_label == "ALL" else sel_day_label, days_map)

# ---------- header actions ----------
c1, c2, c3, c4, c5, c6 = st.columns([2,2,2,2,2,2])

with c1:
    new_mats = st.number_input("Mats", 1, 12, mats, 1)
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("💾 Save", key="save_mats", use_container_width=True):
        mats = int(new_mats)
        for f in finals:
            if f.get("is_break"):
                f["mat"] = min(max(1, f["mat"]), mats)
            else:
                if f["mat"] > mats:
                    f["mat"] = 0
                    f["assigned"] = False
        _reindex_orders_by_mat(finals, mats)
        _save_fb(mats, finals)
        st.rerun()

with c2:
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("🔄 Auto-balance", key="auto", use_container_width=True):
        ordered = list(finals)
        ids_visibles = {f.get("category_id") for f in visible_finals if not f.get("is_break")}
        seq = [f for f in ordered if (not f.get("is_break")) and (sel_day_label == "ALL" or f.get("category_id") in ids_visibles)]
        for i, f in enumerate(seq):
            f["mat"] = (i % mats) + 1
            f["assigned"] = True
        _reindex_orders_by_mat(ordered, mats)
        _save_fb(mats, ordered)
        st.rerun()

with c3:
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("➕ Add Break", key="add_break", use_container_width=True):
        _add_break(finals, 0) # Ajoute à "To Assign" (Mat 0)
        _save_fb(mats, finals)
        st.toast("Break added to 'To Assign'", icon="⏸️")
        st.rerun()

with c4:
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("↩︎ All → To Assign", key="all_to_ua", use_container_width=True):
        ids_visibles = {f.get("category_id") for f in visible_finals if not f.get("is_break")}
        for f in finals:
            if f.get("is_break"):
                continue
            if sel_day_label == "ALL" or f.get("category_id") in ids_visibles:
                f["mat"] = 0
                f["order"] = 0
                f["assigned"] = False
        _save_fb(mats, finals)
        st.rerun()
        
# ... (Export buttons) ...

# Debug info
cnt_breaks = len([f for f in finals if f.get("is_break") and int(f.get("mat",0))==0])
if cnt_breaks > 0:
    st.caption(f"ℹ️ {cnt_breaks} Break(s) currently in 'To Assign'.")


with c5:
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("📄 Export XLS", key="xls", use_container_width=True):
        _go_export("xls", mats, finals, sel_day_label)
with c6:
    st.markdown("<div class='btn-header'></div>", unsafe_allow_html=True)
    if st.button("🖨️ Export PDF", key="pdf", use_container_width=True):
        _go_export("pdf", mats, finals, sel_day_label)

st.divider()

# ---------- Par tapis (KANBAN DRAG & DROP) ----------
from streamlit_sortables import sort_items

cats_map = _cats_by_id()

# Préparation pour sort_items
item_lookup = {}  # { "LabelUnique": item_dict }
kanban_data = []

# Compteur global pour garantir unicité unique si besoin
global_counter = 0

# Colonnes: 0=ToAssign, 1..N=Mats
# On inclut TOUTES les colonnes : 0 (To Assign) + 1..N (Mats)
for m in range(0, mats + 1):
    if m == 0:
        header_label = "📥 To Assign"
        # Items tapis 0 (Breaks inclus !)
        # CORRECTION : On doit afficher les breaks aussi dans To Assign
        mat_items = [f for f in visible_finals if int(f.get("mat", 0)) == 0]
    else:
        header_label = f"Mat {m}"
        # Items du tapis m
        items_all = _mat_items(finals, m)
        ids_visibles = {f.get("category_id") for f in visible_finals if not f.get("is_break")}
        mat_items = [it for it in items_all if it.get("is_break") or sel_day_label == "ALL" or it.get("category_id") in ids_visibles]
    
    col_labels = []
    for it in mat_items:
        if it.get("is_break"):
            base_label = "⏸️ BREAK"
        else:
            cid = it.get("category_id")
            base_label = (cats_map.get(cid) or {}).get("title", cid)
        
        # ASTUCE: Labels uniques mais propres
        # On ajoute des zero-width spaces pour l'unicité React sans pollution visuelle
        invis_suffix = "\u200b" * (global_counter + 1)
        global_counter += 1
        
        unique_label = f"{base_label}{invis_suffix}"
        
        item_lookup[unique_label] = it
        col_labels.append(unique_label)
        
    kanban_data.append({'header': header_label, 'items': col_labels})

# 2. Affichage du Widget Sortable
st.markdown("### 🖐️ Drag & Drop Board")
st.caption("Drag items between columns to assign/unassign or reorder. Manage breaks at the bottom of the page.")


# CSS personnalisé
# On injecte des règles pour forcer le LAYOUT :
# La colonne "To Assign" (la première) doit passer en 100% largeur (Top),
# et les autres (Tapis) restent en dessous côte à côte.
custom_css = """
.sortable-item {
    background-color: #1e293b;
    border: 1px solid #334155;
    color: #f8fafc;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 6px;
    font-size: 0.9rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.sortable-item:hover {
    background-color: #334155;
    border-color: #475569;
    cursor: grab;
}
body > div {
    display: flex !important;
    gap: 12px !important;
    padding: 2px !important;
}
body > div > div:nth-child(1) {
    flex: 1 1 100% !important;
    min-width: 98% !important;
    order: 1 !important; 
    margin-bottom: 5px !important;
    background-color: transparent !important;
    border: none !important;
}
body > div > div:nth-child(1) > div:first-child {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    background-color: #dc2626 !important;
    color: white !important;
    font-weight: 900 !important;
    font-size: 1.3rem !important;
    text-transform: uppercase !important;
    padding: 12px !important;
    border-radius: 6px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
}
body > div > div:nth-child(n+2) {
    flex: 0 0 calc(33.33% - 12px) !important;
    min-width: 250px !important;
    order: 2 !important;
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 10px !important;
}
body > div > div:nth-child(n+2) > div:first-child {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    background-color: #1e3a8a !important;
    color: #bfdbfe !important;
    font-weight: 800 !important;
    font-size: 1.2rem !important;
    padding: 10px !important;
    border-radius: 6px !important;
    margin-bottom: 15px !important;
    border: 1px solid #1e40af !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
}
"""

sorted_data = sort_items(kanban_data, multi_containers=True, direction="vertical", custom_style=custom_css, key="kanban_board_headers_v6")

# 3. Logique de mise à jour
if sorted_data != kanban_data:
    changed = False
    
    for m_idx, mat_data in enumerate(sorted_data):
        # m_idx de 0 à mats (pas de trash)
        current_mat = m_idx 
        
        col_labels = mat_data.get('items', [])
        
        for order_idx, label in enumerate(col_labels):
            found = item_lookup.get(label)
            
            if found:
                # Cas normal : update mat/order
                if found["mat"] != current_mat or found.get("order") != order_idx:
                    found["mat"] = current_mat
                    found["order"] = order_idx
                    # Si mat != 0 => Assigned = True
                    found["assigned"] = (current_mat != 0)
                    changed = True
    
    if changed:
        # Nettoyage des items marqués pour suppression
        finals[:] = [f for f in finals if not f.get("_DELETE_ME")]
        
        _save_fb(mats, finals)
        st.rerun()

st.markdown("---")

# ---------- GESTION DES BREAKS (LIST TYPE) ----------
# On le met en bas pour ne pas perturber le layout du haut
breaks_list = [f for f in finals if f.get("is_break")]
if breaks_list:
    st.markdown("### 🗑️ Manage Breaks")
    st.caption("Click the X to remove a break.")
    if st.button("Delete ALL Breaks", key="del_all_breaks", type="secondary"):
        finals[:] = [f for f in finals if not f.get("is_break")]
        _reindex_orders_by_mat(finals, mats)
        _save_fb(mats, finals)
        st.rerun()
        
    for bk in breaks_list:
        b_mat = int(bk.get("mat", 0))
        b_loc = "In 'To Assign'" if b_mat == 0 else f"On Mat {b_mat}"
        c_bk1, c_bk2 = st.columns([6, 1])
        with c_bk1:
            st.info(f"Break ({b_loc})", icon="⏸️")
        with c_bk2:
            st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)
            if st.button("❌", key=f"del_bk_{bk.get('id')}", help="Delete this break"):
                _delete_break(finals, bk.get('id'))
                _reindex_orders_by_mat(finals, mats)
                _save_fb(mats, finals)
                st.rerun()


# ---------- outils ----------
with st.expander("Advanced tools", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Rebuild orders", use_container_width=True):
            _reindex_orders_by_mat(finals, mats)
            _save_fb(mats, finals)
            st.rerun()
    with c2:
        if st.button("🗑️ Reset Final Block (Clear All)", type="primary", use_container_width=True):
            _save_fb(mats, [])
            st.toast("Final Block has been reset!", icon="🗑️")
            st.rerun()

# FORCE RELOAD 1
