# pages/04_Assignation.py
from __future__ import annotations
import streamlit as st

from ui import apply_theme
from settings_io import load_settings
from storage import load_all, save, load
from keyer import ukey  # ukey pour les boutons généraux (pas pour les VIP)

PAGE_KEY   = "assignation"
TOGGLE_KEY = "assign_show_assigned"   # clé du widget toggle
DIM_SET_KEY = "assign_dimmed_ids"     # catégories “validées ici” (assombries)
FORCE_ON   = "_assign_force_show_on"  # flags non-widget pour piloter le toggle au prochain run
FORCE_OFF  = "_assign_force_show_off"
JUST_CLEARED = "_assign_just_cleared_pid"  # pid vidé à traiter au prochain run

st.set_page_config(page_title="Assignation", page_icon="assets/vip_assignment.png", layout="wide")
cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()


# --- CSS global (badge & wrapper sombre) ---
st.markdown("""
<style>
.badge-valid {
  display:inline-block; padding:2px 8px; border-radius: 999px;
  font-size:12px; line-height:1; background: rgba(0,0,0,.65); color:#fff;
  margin-left:8px; vertical-align: middle;
}
.dim-wrap { opacity:.45; }
.title-line { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
</style>
""", unsafe_allow_html=True)

c_ico, c_tit = st.columns([1, 15])
with c_ico:
    st.image("assets/vip_assignment.png", width=50)
with c_tit:
    st.title("VIP Assignation")

def persist_assign(assign: dict):
    """Écrit immédiatement assignment.json depuis {category_id: [vip_ids...]}."""
    new_list = [{"category_id": k, "vip_ids": v} for k, v in assign.items()]
    save("assignment", new_list)

# -------- Préparation état session (AVANT widgets) --------
if DIM_SET_KEY not in st.session_state:
    st.session_state[DIM_SET_KEY] = set()

# Appliquer les flags de forçage AVANT de créer le toggle
if st.session_state.get(FORCE_ON):
    st.session_state[TOGGLE_KEY] = True
    del st.session_state[FORCE_ON]
if st.session_state.get(FORCE_OFF):
    st.session_state[TOGGLE_KEY] = False
    del st.session_state[FORCE_OFF]

# Traiter un éventuel "vider VIP" du run précédent, AVANT les widgets
pid_cleared = st.session_state.get(JUST_CLEARED)
if pid_cleared:
    st.session_state[DIM_SET_KEY].discard(pid_cleared)  # plus "Validée"
    st.session_state[TOGGLE_KEY] = False                # retour vue par défaut (non assignées)
    del st.session_state[JUST_CLEARED]
    st.success(f"Assignations vidées pour la catégorie {pid_cleared}.")

# -------- Données --------
data = load_all()
cats = {(c.get("id") or c.get("title")): c for c in (data.get("categories") or [])}
vips = {v.get("id"): v for v in (data.get("vip") or [])}

# Planning: garder uniquement les non réalisées (done=False)
# --- lecture "finals_days" (Distribution) ---
days_map = load("finals_days") or {}
# days_map: {"1": [id...], "2": [id...]}

# Define available options
available_days = sorted(days_map.keys(), key=lambda x: int(x) if x.isdigit() else 999)
filter_opts = ["All"] + [f"Day {d}" for d in available_days]

# UI Filter
c_fil, _ = st.columns([2, 5])
with c_fil:
    sel_filter = st.selectbox("📅 Filter by Day", filter_opts)

# Build planning list based on filter
planning_ids = []
if sel_filter == "All":
    for day_ids in days_map.values():
        planning_ids.extend([str(x) for x in day_ids])
else:
    # "Day X"
    day_key = sel_filter.replace("Day ", "")
    planning_ids = [str(x) for x in days_map.get(day_key, [])]

# Convert to dict objects for compatibility with existing code
# The existing code expects objects, so we wrap the IDs
planning_all = [{"category_id": pid} for pid in planning_ids]

# Deduplicate if "All" (just in case)
if sel_filter == "All":
    seen = set()
    unique = []
    for it in planning_all:
        pid = it["category_id"]
        if pid not in seen:
            unique.append(it)
            seen.add(pid)
    planning_all = unique

# Assignations actuelles
assign_list = data.get("assignment") or []
assign = {a.get("category_id"): list(a.get("vip_ids") or []) for a in assign_list}
# Load roles map: {category_id: {vip_id: "Gold"}}
assign_roles = {a.get("category_id"): dict(a.get("vip_roles") or {}) for a in assign_list}

def persist_assign_with_roles(assign_map, roles_map):
    new_list = []
    for cid, vids in assign_map.items():
        robj = roles_map.get(cid, {})
        new_list.append({
            "category_id": cid, 
            "vip_ids": vids, 
            "vip_roles": robj
        })
    save("assignment", new_list)

# -------- Barre d’outils --------
t1, t2, t3, t4 = st.columns([1, 1, 4, 3])  # adjusted columns
with t1:
    if st.button("♻️ Show All", key=ukey(f"reset_{PAGE_KEY}"), use_container_width=True):
        st.session_state[DIM_SET_KEY] = set()
        st.rerun()
with t2:
    if st.button("💾 Save", key=ukey("save_assign"), use_container_width=True):
        persist_assign_with_roles(assign, assign_roles)
        st.success("Assignments saved.")
        st.rerun()

# Valeur par défaut du toggle si première exécution
if TOGGLE_KEY not in st.session_state:
    st.session_state[TOGGLE_KEY] = False
with t4:
    show_assigned_dim = st.toggle(
        "Show already assigned categories",
        value=st.session_state[TOGGLE_KEY],
        key=TOGGLE_KEY
    )

st.divider()

# Role Selector (Sticky-ish via columns?)
r_col1, r_col2 = st.columns([2, 5])
with r_col1:
    # Use radio for clear selection
    selected_role = st.radio("🏅 Assign VIP as:", ["General", "Gold", "Silver", "Bronze"], horizontal=True)

# -------- Stats --------
total_todo = len(planning_all)
already_assigned = sum(1 for p in planning_all if len(assign.get(p.get("category_id"), [])) > 0)
not_assigned = total_todo - already_assigned
st.caption(f"To Do: {total_todo} • Unassigned: {not_assigned} • Already Assigned (not done): {already_assigned}")

if not planning_all:
    st.info("No matching planning entries.")
    st.stop()

vip_ids_sorted = sorted(vips.keys(), key=lambda vid: (vips.get(vid, {}).get("name") or vid).upper())

def medal_iocs_line(cat: dict) -> str:
    meds = sorted(cat.get("medalists") or [], key=lambda m: int(m.get("rank", 99)))
    parts = []
    for m in meds:
        try:
            r = int(m.get("rank", 99))
        except Exception:
            r = 99
        icon = "🥇" if r == 1 else ("🥈" if r == 2 else "🥉")
        ioc = (m.get("nation") or "").strip()
        if not ioc:
            continue
        parts.append(f"{icon} <code>{ioc}</code>")
    return " &nbsp; ".join(parts) if parts else "<span style='opacity:.6'>(No IOC available)</span>"

def should_show(pid: str, is_assigned: bool) -> bool:
    # non assignée -> afficher ; assignée -> afficher si toggle ON ou marquée “validée ici”
    if not is_assigned:
        return True
    return st.session_state[TOGGLE_KEY] or (pid in st.session_state[DIM_SET_KEY])

# -------- Liste des catégories en attente --------
for it in planning_all:
    pid = it.get("category_id")
    cat = cats.get(pid, {})
    title = cat.get("title") or pid or "—"

    current = assign.get(pid, [])
    current_roles = assign_roles.get(pid, {})
    
    is_assigned = len(current) > 0
    if not should_show(pid, is_assigned):
        continue

    dimmed = (pid in st.session_state[DIM_SET_KEY]) and is_assigned

    # Titre + badge (si validée)
    st.markdown(f"<div class='{'dim-wrap' if dimmed else ''}'>", unsafe_allow_html=True)
    badge_html = " <span class='badge-valid'>Validated</span>" if dimmed else ""
    st.markdown(f"<div class='title-line'><h3 style='margin:0'>{title}</h3>{badge_html}</div>", unsafe_allow_html=True)

    # IOC / médailles
    st.markdown(medal_iocs_line(cat), unsafe_allow_html=True)

    # Ligne VIP remettants (noms + roles)
    if current:
        names_display = []
        for vid in current:
            vname = vips.get(vid, {}).get("name", vid)
            role = current_roles.get(vid)
            if role and role != "General":
                # Add emoji for role
                icon = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}.get(role, "")
                names_display.append(f"{vname} ({icon}{role})")
            else:
                names_display.append(vname)
        st.write("**Presenting VIPs:** " + ", ".join(names_display))
    else:
        st.write("**Presenting VIPs:** (none)")

    # Grille de boutons VIP (ID ; clic = toggle + persist immédiat)
    st.caption(f"Click to assign/unassign as **{selected_role}**:")
    per_row = 8
    row_buf = []

    for i, vid in enumerate(vip_ids_sorted, start=1):
        btn_key = f"vipbtn__{pid}__{vid}"  # clé STABLE
        
        # Determine button label based on assignment status AND role
        if vid in current:
            role = current_roles.get(vid)
            if role and role != "General":
                icon = {"Gold": "🥇", "Silver": "🥈", "Bronze": "🥉"}.get(role, "")
                label = f"✅ {vid} {icon}"
            else:
                label = f"✅ {vid}"
        else:
            label = f"{vid}"
            
        row_buf.append({"label": label, "key": btn_key, "vid": vid})

        if (i % per_row) == 0:
            cols = st.columns(per_row)
            for j, btn in enumerate(row_buf):
                with cols[j]:
                    if st.button(btn["label"], key=btn["key"], use_container_width=True):
                        sel = set(assign.get(pid, []))
                        c_roles = assign_roles.get(pid, {})
                        
                        if btn["vid"] in sel:
                            # If removing, remove from both
                            sel.remove(btn["vid"])
                            if btn["vid"] in c_roles:
                                del c_roles[btn["vid"]]
                        else:
                            # If adding, add to list AND set role
                            sel.add(btn["vid"])
                            if selected_role != "General":
                                c_roles[btn["vid"]] = selected_role
                            elif btn["vid"] in c_roles:
                                # Reset to general if selected generic
                                del c_roles[btn["vid"]]
                                
                        assign[pid] = list(sel)
                        assign_roles[pid] = c_roles
                        persist_assign_with_roles(assign, assign_roles)
                        st.session_state[FORCE_ON] = True
                        st.rerun()
            row_buf = []

    # Dernière ligne incomplète
    if row_buf:
        cols = st.columns(len(row_buf))
        for j, btn in enumerate(row_buf):
            with cols[j]:
                if st.button(btn["label"], key=btn["key"], use_container_width=True):
                    sel = set(assign.get(pid, []))
                    c_roles = assign_roles.get(pid, {})
                    
                    if btn["vid"] in sel:
                        sel.remove(btn["vid"])
                        if btn["vid"] in c_roles:
                            del c_roles[btn["vid"]]
                    else:
                        sel.add(btn["vid"])
                        if selected_role != "General":
                            c_roles[btn["vid"]] = selected_role
                        elif btn["vid"] in c_roles:
                            del c_roles[btn["vid"]]

                    assign[pid] = list(sel)
                    assign_roles[pid] = c_roles
                    persist_assign_with_roles(assign, assign_roles)
                    st.session_state[FORCE_ON] = True
                    st.rerun()

    # Actions de ligne
    c1, c2 = st.columns([1, 1])
    with c1:
        # “Valider ici” : assombrir + badge, sans masquer
        if st.button("✅ Validate here", key=ukey(f"val_{PAGE_KEY}_{pid}"), use_container_width=True):
            st.session_state[DIM_SET_KEY].add(pid)
            st.session_state[FORCE_ON] = True
            st.rerun()
    with c2:
        clear_key = f"clearbtn__{pid}"
        if st.button("🗑️ Clear VIP", key=clear_key, use_container_width=True):
            assign[pid] = []
            assign_roles[pid] = {}  # Clear roles too
            persist_assign_with_roles(assign, assign_roles)
            st.session_state[DIM_SET_KEY].discard(pid)
            st.session_state[JUST_CLEARED] = pid
            st.rerun()

    st.divider()
    st.markdown("</div>", unsafe_allow_html=True)
