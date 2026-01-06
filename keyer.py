# keyer.py
from __future__ import annotations
import streamlit as st

def ukey(base: str) -> str:
    d = st.session_state.setdefault("_ukey_counts", {})
    n = d.get(base, 0) + 1
    d[base] = n
    return f"{base}__{n}"
