# pages/01_VIP.py
import base64
from pathlib import Path
import html
import streamlit as st

from settings_io import load_settings
from storage import load_all, save
from ui import apply_theme

st.set_page_config(page_title="VIP", page_icon="🧑‍⚖️", layout="wide")
cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()


st.title("🧑‍⚖️ VIP")

data = load_all()
vips = data.get("vip") or []

APP_ROOT = Path(__file__).parents[1]
PHOTOS_DIR = APP_ROOT / "assets" / "photos"
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Query params helpers ----------
def get_query_params():
    try:
        return dict(st.query_params)
    except Exception:
        return st.experimental_get_query_params()

def set_query_params(**kwargs):
    try:
        st.query_params.clear()
        for k, v in kwargs.items():
            if v is not None:
                st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**{k: v for k, v in kwargs.items() if v is not None})

qp = get_query_params()
edit_id = None
if "edit" in qp:
    val = qp["edit"]
    edit_id = val if isinstance(val, str) else (val[0] if val else None)

# ---------- Utils photos ----------
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

def initials(name: str) -> str:
    parts = [x for x in (name or "").split() if x.strip()]
    if not parts: return "?"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else parts[0][1:2])).upper()

AV_SIZE = 120  # taille fixe des vignettes (largeur/hauteur)

# ---------- Formulaire : édition si edit_id, sinon ajout ----------
st.divider()
if edit_id:
    st.subheader("✏️ Edit a VIP")
    current = next((v for v in vips if v.get("id") == edit_id), None)
    if not current:
        st.warning("VIP not found.")
    else:
        with st.form("edit_vip"):
            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                eid = st.text_input("ID (unique)", value=current.get("id",""))
                ename = st.text_input("Full Name", value=current.get("name",""))
            with c2:
                erole = st.text_input("Role (optional)", value=current.get("role",""))
                eioc  = st.text_input("IOC (e.g. FRA)", value=(current.get("ioc","") or "").upper()).upper().strip()
            with c3:
                if cfg.vip_show_photos:
                    eupload = st.file_uploader("Photo (png/jpg)", type=["png","jpg","jpeg"], key="edit_upl")
                else:
                    eupload = None
                    st.caption("Photos are hidden (see Settings).")
            save_btn = st.form_submit_button("💾 Save changes")
        if save_btn:
            if not eid:
                st.error("ID required.")
            else:
                for v in vips:
                    if v.get("id") == edit_id:
                        v.update({"id": eid, "name": ename, "role": erole, "ioc": eioc})
                        break
                if eupload and eid:
                    ext = Path(eupload.name).suffix.lower() or ".jpg"
                    (PHOTOS_DIR / f"{eid}{ext}").write_bytes(eupload.getbuffer())
                    for v in vips:
                        if v.get("id") == eid:
                            v["photo"] = f"assets/photos/{eid}{ext}"
                save("vip", vips)
                st.success("VIP updated.")
                set_query_params()  # clear ?edit
                st.rerun()

    if st.button("❌ Cancel editing"):
        set_query_params()
        st.rerun()
else:
    st.subheader("➕ Add a VIP")
    with st.form("add_vip"):
        c1, c2, c3 = st.columns([2,2,2])
        with c1:
            new_id = st.text_input("ID (unique)")
            new_name = st.text_input("Full Name")
        with c2:
            new_role = st.text_input("Role (optional)")
            new_ioc  = st.text_input("IOC (e.g. FRA)").upper().strip()
        with c3:
            if cfg.vip_show_photos:
                uploaded = st.file_uploader("Photo (png/jpg)", type=["png","jpg","jpeg"])
            else:
                uploaded = None
                st.caption("Photos are hidden (see Settings).")
        add_btn = st.form_submit_button("Save this VIP")
    if add_btn:
        if not new_id:
            st.error("ID required.")
        else:
            found = next((v for v in vips if v.get("id") == new_id), None)
            if found:
                found.update({"name": new_name, "role": new_role, "ioc": new_ioc})
            else:
                vips.append({"id": new_id, "name": new_name, "role": new_role, "ioc": new_ioc})
            if uploaded:
                ext = Path(uploaded.name).suffix.lower() or ".jpg"
                (PHOTOS_DIR / f"{new_id}{ext}").write_bytes(uploaded.getbuffer())
                for v in vips:
                    if v.get("id") == new_id:
                        v["photo"] = f"assets/photos/{new_id}{ext}"
            save("vip", vips)
            st.success("VIP saved.")
            st.rerun()

st.divider()
st.subheader("VIP List")

# ---------- Liste : cartes avec case à cocher + nom cliquable ----------
if not vips:
    st.info("No VIPs yet.")
else:
    if "vip_selected" not in st.session_state:
        st.session_state.vip_selected = set()

    cols_per_row = 4
    rows = (len(vips) + cols_per_row - 1) // cols_per_row
    idx = 0
    for _ in range(rows):
        cols = st.columns(cols_per_row)
        for col in cols:
            if idx >= len(vips):
                break
            v = vips[idx]; idx += 1
            vid = v.get("id","")
            name = v.get("name", vid)
            role = (v.get("role") or "").strip()
            ioc  = (v.get("ioc")  or "").upper()

            with col:
                # case à cocher sélection suppression
                checked = st.checkbox("", key=f"vip_sel_{vid}", value=(vid in st.session_state.vip_selected))
                if checked:
                    st.session_state.vip_selected.add(vid)
                else:
                    st.session_state.vip_selected.discard(vid)

                # vignette 120x120 uniforme
                if cfg.vip_show_photos:
                    p = resolve_photo_path(v)
                    if p and p.exists():
                        uri = file_to_data_uri(p)
                        if uri:
                            st.markdown(
                                f'<img src="{uri}" alt="{html.escape(name)}" '
                                f'style="width:{AV_SIZE}px;height:{AV_SIZE}px;'
                                f'border-radius:12px;object-fit:cover;object-position:center;">',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f'<div style="width:{AV_SIZE}px;height:{AV_SIZE}px;border-radius:12px;'
                                f'background:#1C2B4A;color:#FFD700;display:flex;align-items:center;'
                                f'justify-content:center;font-weight:700;">{initials(name)}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            f'<div style="width:{AV_SIZE}px;height:{AV_SIZE}px;border-radius:12px;'
                            f'background:#1C2B4A;color:#FFD700;display:flex;align-items:center;'
                            f'justify-content:center;font-weight:700;">{initials(name)}</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.markdown(
                        f'<div style="width:{AV_SIZE}px;height:{AV_SIZE}px;border-radius:12px;'
                        f'background:#1C2B4A;color:#FFD700;display:flex;align-items:center;'
                        f'justify-content:center;font-weight:700;">{initials(name)}</div>',
                        unsafe_allow_html=True
                    )

                # 🔗 nom cliquable -> bascule vers ?edit=<id>
                st.link_button(f"{name}", url=f"?edit={vid}")

                # role / IOC
                if role:
                    st.caption(role)
                if ioc:
                    st.caption(ioc)

    # ---------- Suppressions (sélection + vider) ----------
    st.divider()
    c_del1, c_del2 = st.columns([1,1])
    with c_del1:
        if st.button(f"🗑️ Delete selection ({len(st.session_state.vip_selected)})",
                     disabled=(len(st.session_state.vip_selected) == 0)):
            ids_to_delete = set(st.session_state.vip_selected)
            new_vips = [vv for vv in vips if vv.get("id") not in ids_to_delete]
            save("vip", new_vips)
            st.session_state.vip_selected = set()
            st.success(f"{len(ids_to_delete)} VIP(s) deleted.")
            st.rerun()

    with c_del2:
        confirm = st.checkbox("Yes, I confirm deleting *all* VIPs")
        if st.button("🧹 Clear entire list", type="secondary", disabled=not confirm):
            save("vip", [])
            st.session_state.vip_selected = set()
            st.success("All VIPs have been deleted.")
            st.rerun()
