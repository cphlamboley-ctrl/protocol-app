# pages/14_Import_Categories.py
from __future__ import annotations
import io, re
from typing import List, Dict, Any
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import streamlit as st
import pandas as pd

from ui import apply_theme, render_sidebar
from settings_io import load_settings
from storage import save

st.set_page_config(page_title="Import Categories", page_icon="📥", layout="wide")

cfg = load_settings()
apply_theme()
render_sidebar()

st.title("📥 Import Categories")

KEEP_RX = re.compile(r"(JIU[- ]?JITSU|NE[- ]?WAZA|DUO|SHOW|FIGHTING)", re.IGNORECASE)
SEX_RX  = re.compile(r"^[mfMF]$")

def _read_csv_first_two_cols(file) -> list[dict]:
    """CSV → prend strictement les 2 premières colonnes (ID, Title), corrige M/F, filtre catégories plausibles."""
    raw = file.read()
    df = None
    for enc in ("utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            try:
                df = pd.read_csv(io.StringIO(text), sep=None, engine="python", header=0)
            except Exception:
                df = None
            if df is None or df.shape[1] < 2:
                df = pd.read_csv(io.StringIO(text), sep=None, engine="python", header=None)
            break
        except Exception:
            df = None
    if df is None or df.shape[1] < 2:
        return []

    df = df.iloc[:, :2].copy()
    df.columns = ["id", "title"]
    df["id"] = df["id"].astype(str).str.strip()
    df["title"] = df["title"].astype(str).str.strip()

    df = df[(df["id"] != "") & (df["title"] != "")]
    # auto-fix : si title = M/F mais id = vraie catégorie → title = id
    inv_mask = df["title"].str.match(SEX_RX) & df["id"].str.contains(KEEP_RX)
    df.loc[inv_mask, "title"] = df.loc[inv_mask, "id"]
    # supprime lignes où title reste M/F
    df = df[~df["title"].str.match(SEX_RX)]
    # garde uniquement les titres plausibles
    df = df[df["title"].str.contains(KEEP_RX)]

    # dédoublonnage par id
    seen = set()
    rows = []
    for _, r in df.iterrows():
        cid = r["id"].strip()
        title = r["title"].strip()
        if cid and title and cid not in seen:
            rows.append({"id": cid, "title": title})
            seen.add(cid)
    return rows

# RESET (facultatif, pratique ici)
with st.expander("🧹 Reset categories (and clear related)", expanded=False):
    st.warning("This will empty **Categories**, and also clear **Planning** and **Day assignments**.")
    cols = st.columns([1, 1, 3])
    if cols[0].button("🧨 Reset now", use_container_width=True):
        save("categories", [])
        save("planning", [])
        save("finals_days", {})
        st.success("Reset done.")
        st.rerun()

st.divider()
st.subheader("Choose your import method")

tab_csv, tab_txt, tab_xls, tab_api = st.tabs(["CSV (ID, Title)", "TXT", "XLS/XLSX", "API"])

# CSV
with tab_csv:
    st.caption("We import **exactly** the first two columns: 1) ID, 2) Category name (title).")
    
    example_csv = """id,title
U16-M-46,U16 Male -46kg Jiu-Jitsu
U18-F-52,U18 Female -52kg Fighting
ADULT-M-77,Adult Male -77kg Ne-Waza
DUO-MIX,Duo Mixed
SHOW-OPEN,Show Open"""
    st.download_button("⬇️ Download example CSV", data=example_csv, file_name="categories_example.csv", mime="text/csv")
    
    f = st.file_uploader("Upload CSV", type=["csv"], key="csv_up")
    if f is not None:
        try:
            rows = _read_csv_first_two_cols(f)
            if not rows:
                st.error("No valid rows found (need at least two columns with a real category name).")
            else:
                cats = [{"id": r["id"], "title": r["title"], "medalists": []} for r in rows]
                save("categories", cats)
                st.success(f"Imported {len(cats)} categories from CSV.")
                st.rerun()
        except Exception as e:
            st.error(f"CSV import error: {e}")

# TXT
with tab_txt:
    st.caption("Each valid line must contain: JIU-JITSU / NE-WAZA / DUO / SHOW / FIGHTING.")
    f = st.file_uploader("Upload TXT", type=["txt"], key="txt_up")
    if f is not None:
        try:
            lines = f.read().decode("utf-8", errors="ignore").splitlines()
            rows = []
            seen = set()
            for line in lines:
                t = line.strip()
                if not t: 
                    continue
                if SEX_RX.match(t): 
                    continue
                if not KEEP_RX.search(t):
                    continue
                cid = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "cat"
                if cid in seen:
                    k = 2; base = cid
                    while f"{base}-{k}" in seen:
                        k += 1
                    cid = f"{base}-{k}"
                seen.add(cid)
                rows.append({"id": cid, "title": t})

            cats = [{"id": r["id"], "title": r["title"], "medalists": []} for r in rows]
            if not cats:
                st.error("No valid lines detected.")
            else:
                save("categories", cats)
                st.success(f"Imported {len(cats)} categories from TXT.")
                st.rerun()
        except Exception as e:
            st.error(f"TXT import error: {e}")

# XLS/XLSX
with tab_xls:
    st.caption("Expected columns: **title** (required), **id** (optional).")
    
    # Generate example Excel in memory
    def _get_example_xlsx():
        data = [
            {"id": "U16-M-46",   "title": "U16 Male -46kg Jiu-Jitsu"},
            {"id": "U18-F-52",   "title": "U18 Female -52kg Fighting"},
            {"id": "ADULT-M-77", "title": "Adult Male -77kg Ne-Waza"},
            {"id": "DUO-MIX",    "title": "Duo Mixed"},
            {"id": "SHOW-OPEN",  "title": "Show Open"},
        ]
        df_ex = pd.DataFrame(data)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
             df_ex.to_excel(writer, index=False, sheet_name="Categories")
        return buf.getvalue()

    # Note: openpyxl or xlsxwriter must be installed. 
    # Since pd.read_excel works, openpyxl is likely present.
    # We'll try using default engine or openpyxl if xlsxwriter is missing, 
    # but pandas inside streamlit usually handles to_excel if deps are there.
    # Actually, let's keep it simple: just try default.
    
    try:
        # Create a simple valid buffer
        b_out = io.BytesIO()
        with pd.ExcelWriter(b_out) as writer:
            pd.DataFrame([
                {"id": "U16-M-46",   "title": "U16 Male -46kg Jiu-Jitsu"},
                {"id": "U18-F-52",   "title": "U18 Female -52kg Fighting"},
                {"id": "ADULT-M-77", "title": "Adult Male -77kg Ne-Waza"},
                {"id": "DUO-MIX",    "title": "Duo Mixed"},
                {"id": "SHOW-OPEN",  "title": "Show Open"},
            ]).to_excel(writer, index=False)
        st.download_button("⬇️ Download example XLSX", data=b_out.getvalue(), 
                           file_name="categories_example.xlsx", 
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.warning(f"Could not generate example XLSX: {e}")

    f = st.file_uploader("Upload XLS/XLSX", type=["xls", "xlsx"], key="xls_up")
    sheet = st.text_input("Sheet name (optional, leave empty for first sheet)", value="")
    if f is not None:
        try:
            df = pd.read_excel(f, sheet_name=(sheet or 0))
            recs: List[Dict[str, Any]] = df.to_dict(orient="records")
            rows = []
            seen = set()
            for r in recs:
                title = (r.get("title") or r.get("name") or "").strip()
                if not title:
                    continue
                if SEX_RX.match(title) or not KEEP_RX.search(title):
                    continue
                cid = (r.get("id") or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "cat").strip()
                if cid in seen:
                    k = 2; base = cid
                    while f"{base}-{k}" in seen:
                        k += 1
                    cid = f"{base}-{k}"
                seen.add(cid)
                rows.append({"id": cid, "title": title})

            cats = [{"id": r["id"], "title": r["title"], "medalists": []} for r in rows]
            if not cats:
                st.error("No valid rows found.")
            else:
                save("categories", cats)
                st.success(f"Imported {len(cats)} categories from Excel.")
                st.rerun()
        except Exception as e:
            st.error(f"Excel import error: {e}")

# API
with tab_api:
    st.caption("GET endpoint must return a list like: `[{'id':'...','title':'...'}, ...]` (or `name` as fallback).")
    url = st.text_input("API URL", value="")
    token = st.text_input("Bearer token (optional)", value="", type="password")
    if st.button("🔌 Fetch from API", use_container_width=True):
        if not url.strip():
            st.error("Please provide an API URL.")
        else:
            try:
                import requests
                headers = {"Accept": "application/json"}
                if token.strip():
                    headers["Authorization"] = f"Bearer {token.strip()}"
                r = requests.get(url.strip(), headers=headers, timeout=20)
                r.raise_for_status()
                payload = r.json()
                if isinstance(payload, dict) and "results" in payload:
                    payload = payload["results"]
                if not isinstance(payload, list):
                    st.error("Unexpected JSON format (expecting a list).")
                else:
                    rows = []
                    seen = set()
                    for it in payload:
                        if not isinstance(it, dict):
                            continue
                        title = (it.get("title") or it.get("name") or "").strip()
                        if not title or SEX_RX.match(title) or not KEEP_RX.search(title):
                            continue
                        cid = (it.get("id") or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "cat").strip()
                        if cid in seen:
                            k = 2; base = cid
                            while f"{base}-{k}" in seen:
                                k += 1
                            cid = f"{base}-{k}"
                        seen.add(cid)
                        rows.append({"id": cid, "title": title})

                    cats = [{"id": r["id"], "title": r["title"], "medalists": []} for r in rows]
                    if not cats:
                        st.error("No valid rows found in API response.")
                    else:
                        save("categories", cats)
                        st.success(f"Imported {len(cats)} categories from API.")
                        st.rerun()
            except Exception as e:
                st.error(f"API import error: {e}")
