# Home.py
from __future__ import annotations
import os
import streamlit as st
from ui import apply_theme, render_sidebar, get_pages_config, get_page_url
from settings_io import load_settings

st.set_page_config(page_title="JJIF Podiums Suite", page_icon="🏁", layout="wide")
cfg = load_settings()
apply_theme()
# --- CSS: thème sombre et mise en forme de la sidebar ---
st.markdown("""
<style>
/* ---- Sidebar container ---- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d1b2a 0%, #1b263b 100%);
  color: #f1f5f9 !important;
}
section[data-testid="stSidebar"] * {
  color: #f1f5f9 !important;
}

/* ---- Liens (page_link) ---- */
button[kind="pageLink"] {
  background-color: rgba(255,255,255,0.05) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  color: #f1f5f9 !important;
  border-radius: 6px;
  margin-bottom: 4px;
  transition: all .2s ease-in-out;
}
button[kind="pageLink"]:hover {
  background-color: rgba(255,255,255,0.12) !important;
  border-color: rgba(255,255,255,0.2) !important;
  transform: translateX(3px);
}

/* ---- Section titles ---- */
.sidebar-section { margin: 14px 0; }
.section-title {
  font-weight: 700; font-size: 0.95rem; letter-spacing: .02em;
  display: flex; align-items: center; gap: .5rem;
  margin: 10px 0 8px 0;
  color: #facc15 !important;
}
.section-chip {
  display:inline-block; width:12px; height:12px; border-radius:3px;
}
.sep {
  height: 8px; position: relative; margin: 6px 0 12px 0;
}
.sep::before{
  content:""; position:absolute; left:0; right:0; top:50%; height:1px;
  background: linear-gradient(90deg, rgba(255,255,255,0), rgba(250,204,21,.4), rgba(255,255,255,0));
}

/* ---- Texte des avertissements ---- */
.warn-missing { color: #94a3b8 !important; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


# --- Fallback CSS: hide native multipage nav by default if still visible ---
st.markdown("""
<style>
/* Hides Streamlit's native multipage nav in the sidebar */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { display: none !important; }
/* A bit of air in the custom sidebar */
.sidebar-section { margin: 10px 0 14px 0; }
.section-title {
  font-weight: 700; font-size: 0.95rem; letter-spacing: .02em;
  display: flex; align-items: center; gap: .5rem; margin: 6px 0 6px 0;
}
.section-chip {
  display:inline-block; width:12px; height:12px; border-radius:3px;
}
.sep {
  height: 10px; position: relative; margin: 6px 0 12px 0;
}
.sep::before{
  content:""; position:absolute; left:0; right:0; top:50%; height:2px;
  background: linear-gradient(90deg, rgba(255,255,255,0), rgba(180,180,180,.55), rgba(255,255,255,0));
}
.warn-missing { color: #bbb; font-size: 0.8rem; margin-top: -6px; }
</style>
""", unsafe_allow_html=True)

def link(path: str, label: str, icon: str | None = None):
    """
    Displays a link if the file exists, otherwise a disabled greyed-out button.
    Important: NEVER call st.page_link if the file is missing.
    """
    exists = os.path.exists(path)
    if exists:
        st.page_link(path, label=label, icon=icon or "")
    else:
        st.button(f"{(icon + ' ') if icon else ''}{label}", disabled=True, use_container_width=True)
        st.caption(f"<span class='warn-missing'>⚠️ Missing file: <code>{path}</code></span>", unsafe_allow_html=True)

# ------------------- SIDE MENU -------------------
render_sidebar()

# ------------------- MAIN PAGE -------------------
st.title("Final Block & Podiums Suite")
st.markdown("""
Welcome  
""")

config = get_pages_config()

for section in config:
    st.subheader(f"{section['icon']} {section['header']}")
    
    items = section["items"]
    # 4 columns for cards
    cols = st.columns(4)
    
    for i, item in enumerate(items):
        col = cols[i % 4]
        with col:
            # Link calculation (slug)
            # ex: "pages/01_VIP.py" -> "VIP"
            p = item["path"]
            if not os.path.exists(p):
                # Card disabled if file missing
                title = item['label']
                icon = item['icon'] or "❓"
                desc = item.get('description', 'Missing file')
                html = f"""
                <div class="dashboard-card-inner" style="opacity:0.5; cursor:not-allowed;">
                    <div class="card-icon-box" style="filter:grayscale(1);">{icon}</div>
                    <div class="card-content">
                        <div class="card-title">{title}</div>
                        <div class="card-desc">{desc}</div>
                    </div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
            else:
                # Active card with link
                target_url = get_page_url(p)
                
                title = item['label']
                icon = item['icon'] or ""
                desc = item.get('description', '')
                
                html = f"""
                <a href="{target_url}" target="_self" class="dashboard-card">
                    <div class="dashboard-card-inner">
                        <div class="card-icon-box">{icon}</div>
                        <div class="card-content">
                            <div class="card-title">{title}</div>
                            <div class="card-desc">{desc}</div>
                        </div>
                    </div>
                </a>
                """
                st.markdown(html, unsafe_allow_html=True)
                
    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
