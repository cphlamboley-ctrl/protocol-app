import streamlit as st
from settings_io import load_settings, save_settings
from ui import apply_theme, render_sidebar

# ==============================
# Theme and menu initialization
# ==============================
st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
apply_theme()       # 🔹 Apply global colors (incl. sidebar)
render_sidebar()    # 🔹 Build sidebar (FINALS / PODIUMS / SETTINGS)

# ==============================
# Page Settings
# ==============================
st.title("⚙️ Settings")

st.markdown("Configure general application settings.")

cfg = load_settings()

import os
from PIL import Image

def save_uploaded_file(uploaded_file, filename):
    try:
        if not os.path.exists("assets"):
            os.makedirs("assets")
        with open(os.path.join("assets", filename), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return os.path.join("assets", filename)
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# ────────────── COMPETITION DETAILS ──────────────
st.header("🏆 Competition Details")
col_c1, col_c2 = st.columns(2)
with col_c1:
    comp_name = st.text_input("Competition Name", value=getattr(cfg, "competition_name", ""))
    comp_country = st.text_input("Country", value=getattr(cfg, "competition_country", ""))
    comp_city = st.text_input("City", value=getattr(cfg, "competition_city", ""))
with col_c2:
    # Dates
    from datetime import date
    d_from_def = getattr(cfg, "date_from", None)
    d_to_def = getattr(cfg, "date_to", None)
    
    # Conversion string -> date si nécessaire
    if isinstance(d_from_def, str):
        try: d_from_def = date.fromisoformat(d_from_def)
        except: d_from_def = date.today()
    if isinstance(d_to_def, str):
        try: d_to_def = date.fromisoformat(d_to_def)
        except: d_to_def = date.today()
        
    date_from = st.date_input("Date From", value=d_from_def or date.today(), format="DD/MM/YYYY")
    date_to = st.date_input("Date To", value=d_to_def or date.today(), format="DD/MM/YYYY")

# ────────────── LOGOS ──────────────
st.header("🖼️ Logos")
st.caption("Upload PNG or JPG images. They will be saved in 'assets/' folder.")
col_l1, col_l2 = st.columns(2)

with col_l1:
    st.subheader("Event Logo")
    curr_evt = getattr(cfg, "event_logo", "")
    if curr_evt and os.path.exists(curr_evt):
        st.image(curr_evt, width=100)
    evt_file = st.file_uploader("Upload Event Logo", type=["png", "jpg", "jpeg"], key="u_evt")

with col_l2:
    st.subheader("Federation Logo")
    curr_fed = getattr(cfg, "federation_logo", "")
    if curr_fed and os.path.exists(curr_fed):
        st.image(curr_fed, width=100)
    fed_file = st.file_uploader("Upload Federation Logo", type=["png", "jpg", "jpeg"], key="u_fed")

# ────────────── VISUAL OPTIONS ──────────────
st.header("👁️ Display Options")
col1, col2 = st.columns(2)
with col1:
    show_clubs = st.checkbox("Show club name", value=getattr(cfg, "show_clubs", True))
with col2:
    show_vip_photos = st.checkbox("Show VIP photos (VIP + Hostesses)", value=getattr(cfg, "show_vip_photos", True))



# ────────────── SAVE SETTINGS ──────────────
st.divider()
if st.button("💾 Save all settings", use_container_width=True):
    # Gestion des uploads
    evt_path = getattr(cfg, "event_logo", "")
    if evt_file is not None:
        # Use original filename to avoid browser caching issues
        fname = evt_file.name
        # Sanitize simpler
        fname = "".join(x for x in fname if x.isalnum() or x in "._-")
        saved = save_uploaded_file(evt_file, fname)
        if saved: evt_path = saved

    fed_path = getattr(cfg, "federation_logo", "")
    if fed_file is not None:
        fname = fed_file.name
        fname = "".join(x for x in fname if x.isalnum() or x in "._-")
        saved = save_uploaded_file(fed_file, fname)
        if saved: fed_path = saved

    new_cfg = {
        "competition_name": comp_name,
        "competition_country": comp_country,
        "competition_city": comp_city,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "event_logo": evt_path,
        "federation_logo": fed_path,
        "show_clubs": show_clubs,
        "show_vip_photos": show_vip_photos,
    }
    save_settings(new_cfg)
    st.success("Settings saved successfully ✅")
    st.rerun()
