# pages/10_Import_Results.py
from __future__ import annotations
import re
import io
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import pandas as pd
from typing import List, Dict, Any
import streamlit as st

from ui import apply_theme
from settings_io import load_settings
from storage import load_all, save

try:
    from parsers.results_txt_parser import parse_results_txt_with_stats as parse_with_stats
except Exception:
    parse_with_stats = None
try:
    from parsers.results_txt_parser import parse_results_txt as parse_simple
except Exception:
    parse_simple = None

st.set_page_config(page_title="Import Results", page_icon="📥", layout="wide")
cfg = load_settings()
apply_theme()
from ui import render_sidebar
render_sidebar()

st.title("📥 Import Results")
st.caption("Updates ONLY categories & medalists. (Planning is not modified.)")

# --------------------------------------------------------------------------------
# Helpers / Normalization
# --------------------------------------------------------------------------------
_slug_re = re.compile(r"[^A-Za-z0-9]+")
def slugify(s: str) -> str:
    s = (s or "").strip()
    s = _slug_re.sub("_", s.upper()).strip("_")
    return s or "CAT"

def normalize_category(cat: dict) -> dict:
    title = (cat.get("title") or "").strip()
    cid = (cat.get("id") or "").strip() or slugify(title) or "CAT"
    meds = cat.get("medalists") or []
    try:
        meds = sorted(meds, key=lambda m: int(m.get("rank", 99)))
    except Exception:
        pass
    return {"id": cid, "title": title or cid, "medalists": meds}

def _parse_dataframe(df: pd.DataFrame) -> List[dict]:
    """
    Expects columns: Category, Rank, Name, Nation (optional Club).
    Returns list of category dicts.
    """
    # Normalize inputs
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # Map common names
    col_map = {
        "category": ["category", "cat", "title", "division"],
        "rank": ["rank", "place", "pos", "position", "order"],
        "name": ["name", "athlete", "competitor"],
        "nation": ["nation", "country", "ioc", "team"],
        "club": ["club", "school"]
    }
    
    final_cols = {}
    for target, candidates in col_map.items():
        found = next((c for c in df.columns if c in candidates), None)
        if found:
            final_cols[target] = found
            
    if "category" not in final_cols or "rank" not in final_cols or "name" not in final_cols:
        st.error(f"Missing required columns. Found: {list(df.columns)}. Need at least: Category, Rank, Name.")
        return []

    # Group by category
    cats = {}
    for _, row in df.iterrows():
        cat_name = str(row[final_cols["category"]]).strip()
        if not cat_name or cat_name.lower() == "nan":
            continue
            
        try:
            rank_val = int(pd.to_numeric(row[final_cols["rank"]], errors='coerce') or 0)
        except:
            rank_val = 99
            
        name_val = str(row[final_cols["name"]]).strip()
        nati_val = str(row[final_cols.get("nation", "")]).strip() if "nation" in final_cols else ""
        club_val = str(row[final_cols.get("club", "")]).strip() if "club" in final_cols else ""
        
        if not name_val or name_val.lower() == "nan":
            continue

        if cat_name not in cats:
            cats[cat_name] = []
            
        cats[cat_name].append({
            "rank": rank_val,
            "name": name_val,
            "nation": nati_val if nati_val.lower() != "nan" else "",
            "club": club_val if club_val.lower() != "nan" else ""
        })

    # Convert to list
    results = []
    for c_title, medalists in cats.items():
        results.append({
            "title": c_title,
            "id": slugify(c_title),
            "medalists": medalists
        })
    return results

# --------------------------------------------------------------------------------
# EXAMPLE DATA GENERATORS
# --------------------------------------------------------------------------------
def get_example_csv():
    return """Category,Rank,Name,Nation,Club
U16 Male -46kg,1,John Doe,FRA,Judo Paris
U16 Male -46kg,2,Jane Smith,USA,Team USA
U16 Male -46kg,3,Bob Jones,GBR,London Judo
U18 Female -52kg,1,Emma Stone,CAN,Toronto Club
"""

def get_example_xlsx():
    data = [
        {"Category": "U16 Male -46kg", "Rank": 1, "Name": "John Doe", "Nation": "FRA", "Club": "Judo Paris"},
        {"Category": "U16 Male -46kg", "Rank": 2, "Name": "Jane Smith", "Nation": "USA", "Club": "Team USA"},
        {"Category": "U18 Female -52kg", "Rank": 1, "Name": "Emma Stone", "Nation": "CAN", "Club": "Toronto Club"},
    ]
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return buf.getvalue()

# --------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------
tab_txt, tab_csv, tab_xls, tab_sportdata = st.tabs(["📄 TXT Import", "📊 CSV Import", "📗 Excel Import", "🥋 Sportdata Import"])

# --- TXT TAB ---
with tab_txt:
    st.caption("Standard format: Category title, then lines '1 Name IOC'.")
    
    example_txt = """ADULTS MALE -62 KG
1 JOHN DOE FRA
2 JANE SMITH USA
3 BOB JONES GBR
3 ALICE WONDER DEU

U18 FEMALE -48 KG
1 EMMA STONE CAN
2 LUCY LIU CHN
"""
    st.download_button(
        "📄 Download example TXT",
        data=example_txt,
        file_name="example_results.txt",
        mime="text/plain"
    )
    
    upload_txt = st.file_uploader("Select .txt file", type=["txt"], key="up_txt")
    parsed_txt = []
    stats_txt = None
    
    if upload_txt:
        if not (parse_with_stats or parse_simple):
            st.error("Parser not found.")
        else:
            try:
                content = upload_txt.read().decode("utf-8", errors="replace")
                if parse_with_stats:
                    parsed_txt, stats_txt = parse_with_stats(content)
                else:
                    parsed_txt, stats_txt = (parse_simple(content) or []), None
            except Exception as e:
                st.error(f"Read/Parse error : {e}")

# --- CSV TAB ---
with tab_csv:
    st.caption("Requires columns: **Category**, **Rank**, **Name**. Optional: **Nation**, **Club**.")
    st.download_button(
        "📊 Download example CSV",
        data=get_example_csv(),
        file_name="example_results.csv",
        mime="text/csv"
    )
    
    upload_csv = st.file_uploader("Select .csv file", type=["csv"], key="up_csv")
    parsed_csv = []
    
    if upload_csv:
        try:
            df = pd.read_csv(upload_csv)
            parsed_csv = _parse_dataframe(df)
        except Exception as e:
            st.error(f"CSV Error: {e}")

# --- XLS TAB ---
with tab_xls:
    st.caption("Requires columns: **Category**, **Rank**, **Name**. Optional: **Nation**, **Club**.")
    
    try:
        xlsx_data = get_example_xlsx()
        st.download_button(
            "📗 Download example Excel",
            data=xlsx_data,
            file_name="example_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.warning(f"Generator error: {e}")

    upload_xls = st.file_uploader("Select .xlsx file", type=["xlsx", "xls"], key="up_xls")
    parsed_xls = []
    
    if upload_xls:
        try:
            df = pd.read_excel(upload_xls)
            parsed_xls = _parse_dataframe(df)
        except Exception as e:
            st.error(f"Excel Error: {e}")

# --- SPORTDATA TAB ---
with tab_sportdata:
    st.caption("Import CSV exported from Sportdata. Expected columns: **Category**, **Place**, **Name**, **Nation**, **Club**.")
    
    # Example based on user provided image
    sportdata_example = """Category,Place,Points,Name,NationalIDAthlete,InternationalID,DayOfBirth,Kyu,Dan,Club,NationalID,Nation,Federal_Asso,Federal_Asso,Measurement,Comment
ADULTS JIU-JITSU FEMALE -45 KG,1,1000,ORTIKBOEVA RAYKHONA,,UZB00161,25/08/2005,,,JIU-JITSU FEDERATION OF UZBEKISTAN,,UZBEKISTAN,,,,44.9,
ADULTS JIU-JITSU FEMALE -45 KG,2,1000,PHUNG THI HUE,,VIE00046,24/04/1993,,,VIETNAM JUJITSU FEDERATION,,VIETNAM,,,,0.0,"""

    st.download_button(
        "📊 Download Sportdata example CSV",
        data=sportdata_example,
        file_name="sportdata_example.csv",
        mime="text/csv"
    )
    
    upload_sd = st.file_uploader("Select Sportdata .csv file", type=["csv"], key="up_sd")
    parsed_sd = []
    
    if upload_sd:
        try:
            # Sportdata often uses comma, but let's allow pandas to sniff (sep=None)
            # This handles comma (,), semicolon (;), tab (\t), etc.
            df_sd = pd.read_csv(upload_sd, sep=None, engine='python')
            # The generic parser handles "Place" -> "Rank", "Category" -> "Category", etc.
            parsed_sd = _parse_dataframe(df_sd)
        except Exception as e:
            st.error(f"Sportdata CSV Error: {e}")

# --------------------------------------------------------------------------------
# MERGE LOGIC (COMMON)
# --------------------------------------------------------------------------------
final_parsed = parsed_txt or parsed_csv or parsed_xls or parsed_sd

if final_parsed:
    normalized = [normalize_category(c) for c in final_parsed]
    st.markdown("---")
    st.success(f"✅ {len(normalized)} category(ies) detected.")

    if stats_txt:
        st.info(
            f"**Stats** — lines: {stats_txt.get('lines_rank_like',0)}, "
            f"imported: {stats_txt.get('imported_medalists',0)}, "
            f"no IOC: {stats_txt.get('no_ioc',0)}."
        )

    with st.expander("👁️ Preview Data", expanded=False):
        for c in normalized:
            title = c.get("title", c.get("id"))
            meds = c.get("medalists") or []
            st.markdown(f"**{title}** ({len(meds)} medalists)")
            for m in meds:
                medal = "🥇" if str(m.get("rank"))=="1" else ("🥈" if str(m.get("rank"))=="2" else "🥉")
                xtra = f"[{m.get('nation')}]" if m.get('nation') else ""
                st.text(f"  {medal} {m.get('name')} {xtra}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 Merge with existing", use_container_width=True):
            data = load_all()
            cats = data.get("categories") or []
            # Index by ID or Title
            index = {}
            for i, c in enumerate(cats):
                k = (c.get("id") or c.get("title") or "").strip()
                if k: index[k] = i
                
            for inc in normalized:
                key = (inc.get("id") or inc.get("title") or "").strip()
                if key in index:
                    # Update existing
                    idx = index[key]
                    cats[idx]["medalists"] = inc["medalists"]
                    # Update title if present
                    if inc.get("title"): cats[idx]["title"] = inc["title"]
                else:
                    # Append new
                    cats.append(inc)
            
            save("categories", cats)
            st.success("Merge done.")
            
    with c2:
        confirm = st.checkbox("Confirm TOTAL replacement")
        if st.button("🧹 Replace ALL", disabled=not confirm, use_container_width=True):
            save("categories", normalized)
            st.success("Replacement done.")
            
    st.divider()
    with st.expander("🗑️ Danger Zone: Reset Data", expanded=False):
        col_res, col_plan, col_cat = st.columns(3)
        
        # --- Column 1: Clear Results ---
        with col_res:
            st.warning("1. Clear Results")
            st.caption("Removes **medalists** only. Planning safe.")
            if st.checkbox("Confirm results reset", key="chk_res"):
                if st.button("🧨 Clear Results", use_container_width=True):
                    data = load_all()
                    cats = data.get("categories") or []
                    for c in cats:
                        c["medalists"] = []
                    save("categories", cats)
                    st.success("Results cleared.")
                    st.rerun()

        # --- Column 2: Clear Final Block Info (Planning) ---
        with col_plan:
            st.warning("2. Clear Final Block / Planning")
            st.caption("Resets **schedule** (days/order). Categories safe.")
            if st.checkbox("Confirm planning reset", key="chk_plan"):
                if st.button("🗓️ Clear Planning", use_container_width=True):
                    # Reset finals_days
                    save("finals_days", {})
                    st.success("Planning/Final Block info cleared.")
                    st.rerun()

        # --- Column 3: Delete Categories ---
        with col_cat:
            st.error("3. Delete Categories")
            st.caption("⚠️ **DELETES EVERYTHING**.")
            if st.checkbox("Confirm full delete", key="chk_cat"):
                if st.button("💀 Delete ALL", use_container_width=True):
                    save("categories", [])
                    save("finals_days", {})
                    save("assignment", [])
                    st.success("All data deleted.")
                    st.rerun()

    st.info("Go to **Planning** to organize these categories.")

