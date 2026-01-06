from __future__ import annotations
import streamlit as st
from ui import apply_theme, render_sidebar
from settings_io import load_settings
from storage import load

st.set_page_config(page_title="Planning", page_icon="📆", layout="wide")

cfg = load_settings()
apply_theme()
render_sidebar()

st.title("📆 Planning")

cats = load("categories") or []
cats_by_id = {str(c.get("id")): c for c in cats}

# Load distribution by day
days_map = load("finals_days") or {}
# days_map structure: {"1": ["cat_id", ...], "2": ...}

if not days_map:
    st.info("No distribution found. Go to **Distribution Categories / Day** to assign categories to days.")
    
    # Fallback: Show all categories if no days distributed
    if cats:
        st.subheader("All Categories (Undistributed)")
        for c in cats:
            st.markdown(f"- **{c.get('title')}**")
    st.stop()

st.success(f"Found distribution for {len(days_map)} day(s).")

# Sort days (assuming keys are "1", "2", etc.)
try:
    sorted_days = sorted(days_map.keys(), key=lambda x: int(x))
except:
    sorted_days = sorted(days_map.keys())

for d in sorted_days:
    cat_ids = days_map.get(d, [])
    st.markdown(f"### 🗓️ Day {d}")
    
    if not cat_ids:
        st.caption("No categories assigned.")
        continue
        
    for i, cid in enumerate(cat_ids, 1):
        c = cats_by_id.get(str(cid))
        if c:
            st.markdown(f"{i}. **{c.get('title')}**")
        else:
            st.markdown(f"{i}. *Unknown Category ID: {cid}*")
            
    st.divider()

# Check for unassigned
assigned_ids = set()
for ids in days_map.values():
    assigned_ids.update([str(x) for x in ids])

unassigned = [c for c in cats if str(c.get("id")) not in assigned_ids]
if unassigned:
    st.subheader("⚠️ Unassigned Categories")
    for c in unassigned:
        st.markdown(f"- {c.get('title')}")
