# ui.py
import streamlit as st
import os
from pathlib import Path

import base64

# ============================================================
# 🎨 Thème global JJIF + Sidebar customisée
# ============================================================

def get_img_tag(path: str, width: str = "100%", invert: bool = False, clip_circle: bool = False) -> str:
    """
    Read file, base64 encode it, and return an img tag.
    :param invert: if True, applies filter: invert(1); mix-blend-mode: screen;
    :param clip_circle: if True, applies border-radius: 50%; to crop corners (useful for circular icons with white corners).
    """
    try:
        if not os.path.exists(path):
            return "❓"
        with open(path, "rb") as f:
            data = f.read()
        raw_b64 = base64.b64encode(data).decode()
        
        style = f"width:{width}; height:auto; object-fit:contain;"
        if invert:
            style += " filter: invert(1); mix-blend-mode: screen;"
        
        if clip_circle:
            style += " border-radius: 50%;"
            
        return f'<img src="data:image/png;base64,{raw_b64}" style="{style}">'
    except Exception:
        return "❓"

def apply_theme():
    """
    Applique le thème "Glassmorphism" moderne :
    - Fond dégradé profond
    - Sidebar translucide (blur)
    - Typographie 'Outfit'
    - Boutons avec gradients et ombres douces
    """
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

      /* ----------- FOND GÉNÉRAL ----------- */
      html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 0%, #1e293b 0%, #0f172a 50%, #020617 100%) !important;
        color: #f1f5f9 !important;
        font-family: 'Outfit', sans-serif !important;
      }
      [data-testid="stHeader"] { background: transparent !important; }

      /* ----------- SIDEBAR GLASSMORPHISM ----------- */
      [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.65) !important; /* Semi-transparent */
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding-top: 2rem !important;
      }
      [data-testid="stSidebar"] * {
        color: #94a3b8 !important;
      }
      [data-testid="stSidebarNav"] { display: none !important; }

      /* ----------- TITRES ET TEXTES ----------- */
      h1, h2, h3, h4, h5, h6 {
        color: #f8fafc !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
      }
      p, label, span, div {
        color: #e2e8f0;
      }

      /* ----------- SIDEBAR LIENS ----------- */
      [data-testid="stSidebar"] .section-title {
        color: #facc15 !important; /* Gold/Yellow pop */
        text-transform: uppercase;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        margin: 24px 0 8px 8px !important;
      }

      /* Boutons & Liens sidebar */
      [data-testid="stSidebar"] button,
      [data-testid="stSidebar"] a {
        text-decoration: none !important;
        background: transparent !important;
        color: #cbd5e1 !important;
        border: 1px solid transparent !important;
        text-align: left !important;
        transition: all 0.2s ease !important;
        padding: 0.5rem 0.75rem !important;
        display: block !important;
        width: 100% !important;
        border-radius: 6px !important; 
      }
      [data-testid="stSidebar"] button:hover,
      [data-testid="stSidebar"] a:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        transform: translateX(4px);
      }
      /* Séparateur discret */
      .sidebar-sep {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 16px 0;
      }

      /* ----------- BOUTONS MODERNES ----------- */
      /* Primary (défaut) */
      div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2), 0 2px 4px -1px rgba(37, 99, 235, 0.1) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
      }
      div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4), 0 4px 6px -2px rgba(37, 99, 235, 0.2) !important;
        filter: brightness(1.1);
      }
      div.stButton > button:active {
        transform: translateY(0);
      }

      /* Secondary / Disabled override if needed specifically */
      div.stButton > button:disabled {
        background: #334155 !important;
        color: #64748b !important;
        box-shadow: none !important;
        cursor: not-allowed;
        transform: none !important;
      }

      /* ----------- INPUTS & CARDS ----------- */
      div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: white !important;
      }
      div[data-baseweb="input"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
      }
      
      /* ----------- DASHBOARD CARDS (ACCUEIL) ----------- */
      a.dashboard-card {
        text-decoration: none;
        color: inherit;
        display: block;
      }
      .dashboard-card-inner {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 16px;
        transition: all 0.25s ease;
        height: 100%;
        min-height: 90px;
      }
      .dashboard-card-inner:hover {
        background-color: rgba(30, 41, 59, 0.7);
        border-color: rgba(59, 130, 246, 0.5); /* Blue glow */
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.3);
      }
      
      .card-icon-box {
        width: 48px;
        height: 48px;
        min-width: 48px;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        color: white;
      }
      
      .card-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      
      .card-title {
        font-weight: 600;
        font-size: 1.05rem;
        color: #f1f5f9;
        line-height: 1.2;
      }
      
      .card-desc {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.3;
      }
      
      /* ----------- SIDEBAR MIX CARD ----------- */
      a.sidebar-card {
        text-decoration: none;
        color: inherit;
        display: block;
        margin-bottom: 8px;
      }
      .sidebar-card-inner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.2s ease;
        border: 1px solid transparent;
      }
      .sidebar-card-inner:hover {
        background-color: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.1);
        transform: translateX(4px);
      }
      
      .sidebar-icon-box {
        width: 32px;
        height: 32px;
        min-width: 32px;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        color: white;
      }
      
      .sidebar-label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #e2e8f0;
      }

      /* Expander */
      .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.5) !important;
        border-radius: 8px !important;
      }

    </style>
    
    <!-- PAGE FOOTER (COPYRIGHT) -->
    <div style="position:fixed; bottom:10px; left:0; right:0; width:100%; text-align:center; color:#64748b; font-size:0.75rem; background:transparent; z-index:99999; pointer-events:none;">
      (c) 2025 - C. Lamboley
    </div>

    """, unsafe_allow_html=True)


# ============================================================
# 🧭 MENU LATÉRAL PERSONNALISÉ
# ============================================================

def get_pages_config():
    """Retourne la configuration centralisée des pages et sections."""
    # Chemin dynamique pour l'export
    export_path = "pages/12_Final_Block_Export_From_Template.py" if Path("pages/12_Final_Block_Export_From_Template.py").exists() else "pages/12_Final_Block_Export.py"

    # L'image personnalisée pour VIP Assignation (on inverse)
    vip_icon = get_img_tag("assets/vip_assignment.png", width="70%", invert=True)

    # L'image personnalisée pour Prep Room (pas d'inversion mais CLIP CIRCLE pour virer le blanc)
    prep_icon = get_img_tag("assets/prep_room.png", width="70%", invert=False, clip_circle=True)

    # Icone View Categories
    view_cat_icon = get_img_tag("assets/view_categories.png", width="70%", invert=True)

    # Icone Hostess (Hotesse)
    hostess_icon = get_img_tag("assets/hostess.png", width="70%", invert=False, clip_circle=True)

    # Icone Final Block
    final_block_icon = get_img_tag("assets/final_block.png", width="70%", invert=True)

    return [
        {
            "header": "1/2. Creation & Settings",
            "icon": "🛠️",
            "items": [
                {"path": "pages/00_Settings.py", "label": "Global Settings", "icon": "⚙️", "description": "General application configuration."},
                {"path": "pages/09_API_Settings.py", "label": "API Settings", "icon": "🔌", "description": "External API connection."},
                {"path": "pages/01_VIP.py", "label": "VIP Management", "icon": "👔", "description": "Manage officials and guests."},
            ]
        },
        {
            "header": "3. Data Import",
            "icon": "📥",
            "items": [
                {"path": "pages/14_Import_Categories.py", "label": "Import Categories", "icon": "🗂️", "description": "Import the list of categories."},
                {"path": "pages/10_Import_Results.py", "label": "Import Results", "icon": "📊", "description": "Import sports results."},
                {"path": "pages/02_Categories.py", "label": "View Categories", "icon": view_cat_icon, "description": "View imported categories and medalists."},
            ]
        },
        {
            "header": "4. Final Block Management",
            "icon": "🏁",
            "items": [
                {"path": "pages/13_Distribution_Categories_Day.py", "label": "Distribution / Day", "icon": "🧩", "description": "Distribute categories by day."},
                {"path": "pages/11_Final_Block.py", "label": "Final Block", "icon": final_block_icon, "description": "Manage fight order and breaks."},
                {"path": export_path, "label": "Export / Sheets", "icon": "🖨️", "description": "Generate PDF match sheets."},
            ]
        },
        {
            "header": "5. Podium Session",
            "icon": "🏅",
            "items": [
                {"path": "pages/03_Planning.py", "label": "Global Planning", "icon": "📅", "description": "Overview of the planning."},
                {"path": "pages/04_Assignation.py", "label": "VIP Assignment", "icon": vip_icon, "description": "Assign presenters to podiums."},
                {"path": "pages/07_Prep_Room.py", "label": "Prep Room", "icon": prep_icon, "description": "Call room management."},
                {"path": "pages/08_Hotesse.py", "label": "Hostess Mobile", "icon": hostess_icon, "description": "Mobile interface for VIP hostess."},
                {"path": "pages/06_Speaker.py", "label": "Speaker View", "icon": "🎤", "description": "Interface for the speaker."},
                {"path": "pages/05_Live.py", "label": "Live Screen", "icon": "📺", "description": "Public large screen display."},
            ]
        }
    ]

def get_page_url(path: str) -> str:
    """
    Génère le slug URL Streamlit correct à partir du chemin de fichier.
    Règle: Streamlit retire les numéros de tri (ex: "01_VIP.py" -> "VIP").
    """
    filename = os.path.basename(path)
    # Enlever l'extension
    slug = filename.replace(".py", "")
    # Enlever le préfixe numérique (ex: "01_")
    # On cherche le premier underscore et on prend ce qui suit si le début est numérique
    import re
    # Regex pour enlever "01_" ou "11_" au début
    slug = re.sub(r'^\d+_', '', slug)
    return slug

def render_sidebar():
    """
    Construit le menu latéral en utilisant la configuration centralisée.
    Rendu style "Mini Cards" HTML.
    """
    import os
    config = get_pages_config()

    with st.sidebar:
        # Bouton Retour Accueil
        st.markdown("""
        <a href="." target="_self" class="sidebar-card">
            <div class="sidebar-card-inner">
                <div class="sidebar-icon-box">🏠</div>
                <div class="sidebar-label">HOME DASHBOARD</div>
            </div>
        </a>
        <div class="sidebar-sep"></div>
        """, unsafe_allow_html=True)

        for section in config:
            # Titre de section
            st.markdown(f'<div class="section-title">{section["icon"]} {section["header"]}</div>', unsafe_allow_html=True)
            
            # Liens
            for item in section["items"]:
                p = item["path"]
                if os.path.exists(p):
                    target_url = get_page_url(p)
                    
                    label = item["label"]
                    icon = item["icon"]
                    
                    html = f"""
                    <a href="{target_url}" target="_self" class="sidebar-card">
                        <div class="sidebar-card-inner">
                            <div class="sidebar-icon-box">{icon}</div>
                            <div class="sidebar-label">{label}</div>
                        </div>
                    </a>
                    """
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    # Bouton désactivé (style minimaliste pour ne pas polluer)
                    st.button(f"{item['icon']} {item['label']}", disabled=True, key=f"dead_{item['label']}")

            
            # Séparateur après chaque section
            st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)
        

