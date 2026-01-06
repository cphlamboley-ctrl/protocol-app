import streamlit as st
from pathlib import Path

from storage import load_all
from settings_io import load_settings
from ui import apply_theme, get_img_tag

st.set_page_config(page_title="Categories", page_icon="assets/view_categories.png", layout="wide")
cfg = load_settings()
apply_theme()  # JJIF
from ui import render_sidebar
render_sidebar()

icon_html = get_img_tag("assets/view_categories.png", width="40px", invert=True)
st.markdown(f"# {icon_html} Categories", unsafe_allow_html=True)

data = load_all()
cats = data.get("categories") or []
id_to_cat = {c.get("id"): c for c in cats}
ids = list(id_to_cat.keys())

if not ids:
    st.info("No available category.")
else:
    sel = st.selectbox("Category", options=ids, index=0 if ids else None)
    if sel:
        c = id_to_cat.get(sel, {}) or {}
        title = c.get("title", "—")
        st.caption("Category name (from data) :")
        st.text(title)

        st.divider()
        st.subheader("Medalists")

        st.markdown(
            """
            <style>
            .medalist-row { display:flex; align-items:center; gap:10px; margin-bottom:4px; color:#000!important; font-weight:500; font-size:1rem; }
            .medalist-nation { color:#fffff!important; font-weight:400; margin-left:6px; }
            .medalist-club { color:#fffff!important; font-style:italic; margin-left:6px; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        app_root = Path(__file__).parents[1]
        medals_dir = app_root / "assets" / "medals"
        gold_img = medals_dir / "gold.png"
        silver_img = medals_dir / "silver.png"
        bronze_img = medals_dir / "bronze.png"

        def medal_icon(rank: int):
            if int(rank) == 1:
                return str(gold_img) if gold_img.exists() else "🥇"
            elif int(rank) == 2:
                return str(silver_img) if silver_img.exists() else "🥈"
            else:
                return str(bronze_img) if bronze_img.exists() else "🥉"

        medalists = c.get("medalists", []) or []
        if not medalists:
            st.caption("_No medals information for this category._")
        else:
            for m in medalists:
                medal_path = medal_icon(m.get("rank", 3))
                if Path(medal_path).exists():
                    img_html = f'<img src="file://{medal_path}" width="26" style="vertical-align:middle;">'
                else:
                    img_html = f'<span style="font-size:1.2em;">{medal_path}</span>'
                name = m.get("name", "—")
                nation = m.get("nation", "")
                club = m.get("club", "")

                row_html = f"""
                <div class="medalist-row">
                    {img_html}
                    <span>{name}</span>
                    <span class="medalist-nation">{nation}</span>
                    <span class="medalist-club">{club}</span>
                </div>
                """
                st.markdown(row_html, unsafe_allow_html=True)
