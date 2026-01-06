import json
import streamlit as st
from api_config_io import load_api, save_api, reset_api
from ui import apply_theme

st.set_page_config(page_title="API Settings", page_icon="🛠️", layout="centered")
apply_theme()  # JJIF global
from ui import render_sidebar
render_sidebar()

st.title("🛠️ API Settings")
st.caption("Configure connection to your API (Sportdata / proxy). Saved in data/api_config.json.")

cfg = load_api()

with st.form("api_form"):
    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input("Base URL", value=cfg.base_url, placeholder="https://example.org/api")
        event_id = st.text_input("Event ID", value=cfg.event_id, placeholder="12345")
        refresh = st.number_input("Refresh (s)", 3, 300, cfg.refresh_sec)
    with col2:
        api_key = st.text_input("API Key / Bearer", value=cfg.api_key, type="password")
        timeout = st.number_input("Request timeout (s)", 1, 60, cfg.timeout_sec)
        auto = st.checkbox("Auto-cycle (Live)", value=cfg.auto_cycle)

    st.markdown("**Additional HTTP Headers** (JSON)")
    extra = st.text_area("extra_headers",
                         value=json.dumps(cfg.extra_headers or {}, ensure_ascii=False, indent=2),
                         height=140, label_visibility="collapsed")
    colS, colR = st.columns(2)
    saved = colS.form_submit_button("💾 Save")
    reset = colR.form_submit_button("🧹 Reset")

if saved:
    try:
        headers = json.loads(extra.strip() or "{}")
        new_cfg = save_api({
            "base_url": base_url.strip(),
            "event_id": event_id.strip(),
            "api_key": api_key.strip(),
            "refresh_sec": int(refresh),
            "timeout_sec": int(timeout),
            "auto_cycle": bool(auto),
            "extra_headers": headers,
        })
        st.success("API Settings saved.")
        st.json({k: v for k, v in new_cfg.__dict__.items() if k != "api_key"})
    except Exception as e:
        st.error(f"Error: {e}")

if reset:
    def_cfg = reset_api()
    st.info("Reset to default values.")
    st.json({k: v for k, v in def_cfg.__dict__.items() if k != "api_key"})
