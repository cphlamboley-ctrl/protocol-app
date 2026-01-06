import os
import io, base64
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import streamlit as st

from ui import apply_theme, render_sidebar
from settings_io import load_settings
from storage import load, save

# ===== PDF (ReportLab) =====
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="Final Block – Export", page_icon="🧾", layout="wide")

cfg = load_settings()
apply_theme()
render_sidebar()

st.title("🧾 Final Block – Export")

# ────────────────── Données ──────────────────
fb: Dict[str, Any] = load("final_block") or {"mats": 1, "finals": []}
mats: int = int(fb.get("mats", 1))
finals: List[Dict[str, Any]] = fb.get("finals", [])

cats = load("categories") or load("finals_categories") or []
cats_map = {}
for c in cats:
    if not isinstance(c, dict):
        continue
    cid = c.get("id") or c.get("cid")
    if not cid:
        continue
    title = c.get("title") or c.get("name") or c.get("Category") or c.get("category") or str(cid)
    cc = dict(c)
    cc["title"] = title
    cats_map[cid] = cc

# En-tête “PJ”
day_label = st.session_state.get("final_block_export_day")
now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

line1 = getattr(cfg, "competition_name", "") or getattr(cfg, "event_name", "")
if not line1: 
    line1 = "PODIUM SOFTWARE"

if day_label and str(day_label).upper() != "NONE":
    line2 = f"DAY {day_label}"
else:
    # If no day label found or 'None', we might want to default to nothing or "DAY ALL"? 
    # User said "day number ... is missing", implying they set it.
    # Let's fallback to session state debug if needed, but for now just robustify 'ALL' handling
    if day_label == "ALL":
         line2 = "DAY: ALL"
    else:
         line2 = ""

st.info(f"**PDF Headers:**\n\n**Line 1:** {line1}\n\n**Line 2:** {line2}\n\n**Footer:** Generated on {now_str}")

c1, c2 = st.columns(2)
with c1:
    time_final_block = st.text_input("Heure Final Block (ex. 15:30)", value="15:30")
with c2:
    time_podiums = st.text_input("Heure Podiums (ex. 16:30)", value="16:30")

st.divider()
preview_inline = st.checkbox("Afficher l’aperçu PDF dans la page", value=False)

if not REPORTLAB_OK:
    st.error("Le module ReportLab n’est pas installé. Exécutez : `pip install reportlab`")
    st.stop()

# ────────────────── Helpers PDF ──────────────────
def _img_reader(rec: Optional[Dict[str, Any]]) -> Optional[ImageReader]:
    if not rec or not rec.get("bytes"):
        return None
    try:
        return ImageReader(io.BytesIO(bytes(rec["bytes"])))
    except Exception:
        return None

def _group_by_mat(finals: List[Dict[str, Any]], mats: int) -> Dict[int, List[Dict[str, Any]]]:
    g = {m: [] for m in range(1, mats+1)}
    for f in finals:
        m = int(f.get("mat", 0))
        if 1 <= m <= mats:
            g[m].append(f)
    for m in g:
        g[m].sort(key=lambda x: x.get("order", 999999))
    return g

def _offer(pdf_bytes: bytes, filename: str):
    st.download_button("⬇️ Télécharger", data=pdf_bytes, file_name=filename,
                       mime="application/pdf", use_container_width=True)
    if preview_inline:
        b64 = base64.b64encode(pdf_bytes).decode("ascii")
        st.components.v1.html(
            f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='900' style='border:none;'></iframe>",
            height=920,
        )

def _draw_logo(c: canvas.Canvas, path: str, x: float, y: float, w: float, h: float):
    if path and os.path.exists(path):
        try:
            c.drawImage(path, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

def _draw_overview_header(c: canvas.Canvas, page_w: float, page_h: float,
                          line1: str, line2: str) -> float:
    """Event (Top) -> Title (Middle) -> Day (Bottom)"""
    top_margin = 15*mm
    # Logos config
    logo_h = 20*mm
    logo_w = 30*mm
    logo_y = page_h - top_margin - logo_h + 5*mm

    # Logos
    evt_logo = getattr(cfg, "event_logo", "")
    fed_logo = getattr(cfg, "federation_logo", "")
    
    _draw_logo(c, evt_logo, 15*mm, logo_y, logo_w, logo_h)
    _draw_logo(c, fed_logo, page_w - 15*mm - logo_w, logo_y, logo_w, logo_h)

    # Text
    current_y = page_h - top_margin
    
    # 1. Event Name
    c.setFont("Helvetica-Bold", 16)
    if line1:
        c.drawCentredString(page_w/2, current_y - 3*mm, line1[:120])
    
    # 2. Main Title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_w/2, current_y - 12*mm, "FINAL BLOCK — OVERVIEW")

    # 3. Day / Subtitle
    c.setFont("Helvetica", 12)
    if line2:
        c.drawCentredString(page_w/2, current_y - 20*mm, line2[:120])

    return current_y - 27*mm

def _draw_time_box(c: canvas.Canvas, cx: float, top_y: float, fb: str, pd: str) -> float:
    """Draws a centered box with timings. Returns height used."""
    if not fb and not pd:
        return 0
    
    # Content
    text = f"Final Block: {fb}   •   Podiums: {pd}"
    
    # Dimensions
    box_w = 120*mm
    box_h = 8*mm
    
    # Draw Box
    c.setLineWidth(0.5)
    # c.setFillColorRGB(0.95, 0.95, 0.95) # Optional grey bg? User didn't ask.
    # c.rect(cx - box_w/2, top_y - box_h, box_w, box_h, fill=1)
    c.rect(cx - box_w/2, top_y - box_h, box_w, box_h) # just border
    
    # Draw Text
    c.setFont("Helvetica-Bold", 11)
    # c.setFillColorRGB(0,0,0)
    c.drawCentredString(cx, top_y - box_h/2 - 1.5*mm, text)
    
    return box_h

def _draw_overview_grid_page(
    c: canvas.Canvas, page_w: float, page_h: float,
    mats_slice: List[Tuple[int, List[Dict[str, Any]]]],
    cats_map: Dict[str, Dict[str, Any]],
    line1: str, line2: str,
    time_fb: str, time_pd: str
):
    """Page avec jusqu’à 3 colonnes; chaque colonne = un tapis; grille avec bordures et cellules vides pour breaks."""
    margin_x = 15*mm
    y_header_end = _draw_overview_header(c, page_w, page_h, line1, line2)
    
    # Time Box
    box_h = _draw_time_box(c, page_w/2, y_header_end - 2*mm, time_fb, time_pd)
    
    # Grid Start
    y_start = y_header_end - 2*mm - box_h - 5*mm

    cols = len(mats_slice)
    col_gap = 8*mm
    col_w = (page_w - 2*margin_x - (cols-1)*col_gap) / cols

    mat_lines: List[List[str]] = []
    max_rows_content = 0
    for _, items in mats_slice:
        lines = []
        for it in items:
            if it.get("is_break"):
                lines.append(" ----- BREAK ----- ")
            else:
                cid = it.get("category_id")
                title = (cats_map.get(cid) or {}).get("title", cid)
                lines.append(title)
        mat_lines.append(lines)
        max_rows_content = max(max_rows_content, len(lines))

    header_h = 7*mm
    row_h    = 6.8*mm
    bottom_margin = 15*mm
    available_h = (y_start - bottom_margin)
    max_rows_fit = int((available_h - header_h) // row_h)
    rows = min(max_rows_content, max_rows_fit)

    # Entêtes MAT
    c.setFont("Helvetica-Bold", 11)
    for i, (mat_idx, _) in enumerate(mats_slice):
        x = margin_x + i*(col_w + col_gap)
        c.rect(x, y_start - header_h, col_w, header_h)
        c.drawCentredString(x + col_w/2, y_start - header_h + 2.1*mm, f"MAT {mat_idx}")

    # Grille
    top_grid_y = y_start - header_h
    c.setFont("Helvetica", 8)
    for r in range(1, rows+1):
        y_line = top_grid_y - r*row_h
        for i in range(cols):
            x = margin_x + i*(col_w + col_gap)
            c.line(x, y_line, x + col_w, y_line)

    for i in range(cols):
        x = margin_x + i*(col_w + col_gap)
        c.line(x, top_grid_y, x, top_grid_y - rows*row_h)
        c.line(x + col_w, top_grid_y, x + col_w, top_grid_y - rows*row_h)
        lines = mat_lines[i]
        for r in range(rows):
            cell_y_top = top_grid_y - r*row_h
            txt = lines[r] if r < len(lines) else ""
            if txt:
                c.drawCentredString(x + col_w/2, cell_y_top - row_h + 2.2*mm, txt)

    # Footer (Timestamp Only)
    c.setFont("Helvetica", 8)
    c.drawCentredString(page_w/2, 10*mm, f"Generated on: {now_str}")

def _split_cols_per_page(n_mats: int) -> List[int]:
    """Max 3 colonnes par page (fidèle à la PJ)."""
    if n_mats <= 3:
        return [n_mats]
    pages = []
    r = n_mats
    while r > 0:
        take = min(3, r)
        pages.append(take)
        r -= take
    return pages

def _build_pdf_overview_grid() -> bytes:
    """Construit le PDF OVERVIEW fidèle à la PJ : grille cadrée; 3 colonnes max par page; breaks = vides."""
    buf = io.BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    grouped = _group_by_mat(finals, mats)
    mats_list = [(m, grouped.get(m, [])) for m in range(1, mats+1) if grouped.get(m, [])]

    if not mats_list:
        _ = _draw_overview_header(c, page_w, page_h, line1, line2)
        c.setFont("Helvetica", 12)
        c.drawCentredString(page_w/2, page_h/2, "Aucune finale à afficher.")
        c.showPage()
        c.save()
        return buf.getvalue()

    pages_cols = _split_cols_per_page(len(mats_list))
    idx = 0
    for take in pages_cols:
        slice_items = mats_list[idx: idx+take]
        _draw_overview_grid_page(c, page_w, page_h, slice_items, cats_map,
                                 line1, line2, time_final_block, time_podiums)
        c.showPage()
        idx += take

    c.save()
    return buf.getvalue()

def _draw_header_block(c: canvas.Canvas, page_w: float, page_h: float,
                       title: str, day_text: str, mat_title: str = "") -> float:
    margin = 15*mm
    top_y = page_h - margin
    
    # Logos config
    logo_h = 18*mm
    logo_w = 25*mm
    logo_y = top_y - 18*mm
    
    evt_logo = getattr(cfg, "event_logo", "")
    fed_logo = getattr(cfg, "federation_logo", "")
    _draw_logo(c, evt_logo, margin, logo_y, logo_w, logo_h)
    _draw_logo(c, fed_logo, page_w - margin - logo_w, logo_y, logo_w, logo_h)

    # 1. Event
    c.setFont("Helvetica-Bold", 16)
    if title:
        c.drawCentredString(page_w/2, top_y - 6*mm, title[:100])
    
    # 2. Mat Title (optional override or specific)
    # If this marks the start of a mat
    if mat_title:
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(page_w/2, top_y - 13*mm, mat_title)
        
    # 3. Day
    if day_text:
        c.setFont("Helvetica", 12)
        c.drawCentredString(page_w/2, top_y - 20*mm, day_text[:100])
        
    c.setLineWidth(1)
    c.line(margin, top_y - 24*mm, page_w - margin, top_y - 24*mm)
    
    # 4. Time Box (using globals)
    box_h = _draw_time_box(c, page_w/2, top_y - 26*mm, time_final_block, time_podiums)
    
    return top_y - 26*mm - box_h - 6*mm

def _draw_mat_page(c: canvas.Canvas, page_w: float, page_h: float, y: float,
                   mat_idx: int, items: List[Dict[str, Any]], cats_map: Dict[str, Dict[str, Any]]):
    margin = 15*mm
    line_h = 9.5*mm
    
    # y provided is start of CONTENT.
    
    c.setFont("Helvetica", 12)
    for it in items:
        # Check page break
        if y < 20*mm:
            # Draw Footer before page break? Or on every page?
            # Footer on previous page
            c.setFont("Helvetica", 8)
            c.drawCentredString(page_w/2, 10*mm, f"Generated on: {now_str}")
            
            c.showPage()
            
            # New page header
            y = _draw_header_block(c, page_w, page_h, line1, line2, mat_title=f"MAT {mat_idx} (suite)")
            c.setFont("Helvetica", 12)
            
        if it.get("is_break"):
            c.setFont("Helvetica-Oblique", 12)
            c.drawString(margin + 8*mm, y, "— Break —")
            c.setFont("Helvetica", 12)
            y -= line_h * 0.8
            continue
            
        cid = it.get("category_id")
        title = (cats_map.get(cid) or {}).get("title", cid)
        # Removed order number as requested
        c.drawString(margin, y, title)
        y -= line_h

    # Footer on last page of mat
    c.setFont("Helvetica", 8)
    c.drawCentredString(page_w/2, 10*mm, f"Generated on: {now_str}")

def _build_pdf_per_mat() -> bytes:
    buf = io.BytesIO()
    page_w, page_h = A4
    c = canvas.Canvas(buf, pagesize=A4)
    grouped = _group_by_mat(finals, mats)
    
    if not any(grouped.values()):
        y = _draw_header_block(c, page_w, page_h, line1, line2, mat_title="NO MATCHES")
        c.setFont("Helvetica", 12)
        c.drawString(20*mm, y, "Aucune finale à exporter.")
        c.showPage()
        c.save()
        return buf.getvalue()
        
    for m in range(1, mats+1):
        items = grouped.get(m, [])
        if not items:
            continue
        # Header First Page of Mat
        y = _draw_header_block(c, page_w, page_h, line1, line2, mat_title=f"MAT {m}")
        _draw_mat_page(c, page_w, page_h, y, m, items, cats_map)
        c.showPage()
    
    c.save()
    return buf.getvalue()

# ────────────────── UI exports ──────────────────
colA, colB = st.columns(2)

with colA:
    st.subheader("📄 Export OVERVIEW (grille cadrée, style PJ)")
    if st.button("Générer PDF OVERVIEW (PJ)", use_container_width=True, key="btn_overview_pj"):
        pdf = _build_pdf_overview_grid()
        _offer(pdf, "final_block_overview.pdf")

with colB:
    st.subheader("📄 Export 1 page = 1 tapis")
    if st.button("Générer PDF par tapis", use_container_width=True, key="btn_permat"):
        pdf = _build_pdf_per_mat()
        _offer(pdf, "final_block_by_mat.pdf")
