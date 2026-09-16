import os
import math
import io
import requests
import re
from fpdf import FPDF
from datetime import datetime
from img_prop_handler import PropertyImage, standardize_image_for_container
from ai_locationAPI import AISummaryGenerator

PAGE_W      = 210
PAGE_H      = 297
MARGIN      = 15
CONTENT_W   = PAGE_W - 2 * MARGIN  # 180mm

MAROON      = (122, 0, 22)    # Brand Maroon #7A0016
GOLD        = (212, 175, 55)   # Gold Accent #D4AF37
DARK_GRAY   = (30, 41, 59)    # Slate Dark #1E293B
MID_GRAY    = (100, 116, 139) # Slate Mid #64748B
LIGHT_GRAY  = (226, 232, 240)# Slate Light #E2E8F0
CARD_BG     = (248, 250, 252) # Light Card #F8FAFC
CREAM_BG    = (254, 252, 232) # Soft Gold/Cream #FEFCE8
WHITE       = (255, 255, 255)


def num_to_words(n: int) -> str:
    if n == 0:
        return "Zero"
        
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    thousands = ["", "Thousand", "Million", "Billion", "Trillion"]
    
    def helper(num):
        if num == 0:
            return []
        elif num < 20:
            return [units[num]]
        elif num < 100:
            return [tens[num // 10]] + helper(num % 10)
        else:
            return [units[num // 100], "Hundred"] + helper(num % 100)
            
    res = []
    i = 0
    while n > 0:
        chunk = n % 1000
        if chunk != 0:
            words = helper(chunk)
            if i > 0:
                words.append(thousands[i])
            res = words + res
        n //= 1000
        i += 1
        
    return " ".join([w for w in res if w])


def amount_to_words(amount_str: str) -> str:
    clean_str = re.sub(r"[^\d]", "", str(amount_str))
    if not clean_str:
        return "Not Provided"
    try:
        val = int(clean_str)
        words = num_to_words(val)
        return f"Sri Lankan Rupees {words} Only"
    except Exception:
        return "Not Provided"


class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        self.alias_nb_pages()

    def header(self):
        if self.page_no() == 1:
            return
        # Professional Institutional Header
        self.set_text_color(*MID_GRAY)
        self.set_font("Arial", "B", 7.5)
        self.cell(0, 8, "PROPIQ  |  PROPERTY VALUATION APPRAISAL REPORT", 0, 0, "L")
        self.set_x(PAGE_W - MARGIN - 80)
        self.cell(80, 8, "DEPARTMENT OF ESTATE MANAGEMENT & VALUATION - USJP", 0, 1, "R")
        self.set_draw_color(*MAROON)
        self.set_line_width(0.4)
        self.line(MARGIN, 14, PAGE_W - MARGIN, 14)
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        # Professional Institutional Footer with Total Page Count
        self.set_draw_color(*LIGHT_GRAY)
        self.set_line_width(0.3)
        self.line(MARGIN, PAGE_H - 14, PAGE_W - MARGIN, PAGE_H - 14)
        self.set_y(PAGE_H - 13)
        self.set_text_color(*MID_GRAY)
        self.set_font("Arial", "I", 8)
        self.cell(0, 9, "Confidential Professional Valuation Document - Powered by Prop IQ", 0, 0, "L")
        self.set_x(PAGE_W - MARGIN - 30)
        self.set_font("Arial", "B", 8)
        self.cell(30, 9, f"Page {self.page_no()} of {{nb}}", 0, 0, "R")

    def _safe_str(self, text) -> str:
        if text is None:
            return "N/A"
        s = str(text)
        s = s.replace("—", "-").replace("–", "-").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        return s.encode("latin-1", errors="replace").decode("latin-1")

    def ensure_space(self, required_h: float):
        """
        Intelligent Page Breaking: Checks remaining space on page.
        If available height is less than required_h, starts a clean new page.
        """
        if self.get_y() + required_h > PAGE_H - 16:
            self.add_page()

    def section_heading(self, title: str):
        # Guarantee heading + accent line + initial paragraph text stay together
        self.ensure_space(28)
        
        curr_y = self.get_y()
        self.set_fill_color(*MAROON)
        self.rect(MARGIN, curr_y, 4.5, 8, "F")
        
        self.set_x(MARGIN + 7)
        self.set_text_color(*MAROON)
        self.set_font("Arial", "B", 11)
        self.cell(CONTENT_W - 7, 8, self._safe_str(title), ln=True)
        
        # Gold divider line
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y() + 1, PAGE_W - MARGIN, self.get_y() + 1)
        self.ln(4)
        self.set_text_color(*DARK_GRAY)

    def sub_heading(self, title: str):
        self.ensure_space(20)
        self.set_x(MARGIN)
        self.set_text_color(*MAROON)
        self.set_font("Arial", "B", 9.5)
        self.cell(CONTENT_W, 6, self._safe_str(title), ln=True)
        self.ln(1)
        self.set_text_color(*DARK_GRAY)

    def report_paragraph(self, text: str):
        self.set_text_color(*DARK_GRAY)
        self.set_font("Arial", "", 9.5)
        
        for block in text.split("\n\n"):
            clean_block = block.strip()
            if not clean_block:
                continue
            # Calculate height required for this paragraph block
            lines = self.get_string_width(clean_block) / (CONTENT_W - 2)
            est_h = max(1, lines) * 5.2 + 4
            self.ensure_space(min(est_h, 35))
            self.multi_cell(CONTENT_W, 5.2, self._safe_str(clean_block))
            self.ln(2.5)

    def guidance_text(self, text: str):
        self.set_text_color(*MID_GRAY)
        self.set_font("Arial", "I", 8.5)
        for line in text.split("\n"):
            if line.strip():
                self.ensure_space(10)
                self.multi_cell(CONTENT_W, 4.5, self._safe_str(line.strip()))
        self.ln(1.5)

    def user_value(self, value):
        self.ensure_space(10)
        if value and str(value).strip() and str(value).strip() != "N/A":
            self.set_text_color(*DARK_GRAY)
            self.set_font("Arial", "", 9.5)
            text = ", ".join(value) if isinstance(value, list) else str(value)
            self.multi_cell(CONTENT_W, 5.2, self._safe_str(text))
        else:
            self.set_text_color(*MID_GRAY)
            self.set_font("Arial", "I", 9)
            self.cell(CONTENT_W, 5.2, "Not Provided", ln=True)
        self.ln(2)

    def divider(self):
        self.set_draw_color(*LIGHT_GRAY)
        self.set_line_width(0.3)
        self.line(MARGIN, self.get_y(), MARGIN + CONTENT_W, self.get_y())
        self.ln(4)

    def render_key_metrics(self, data: dict):
        self.ensure_space(68)
            
        self.set_fill_color(*CARD_BG)
        self.set_draw_color(*LIGHT_GRAY)
        self.set_line_width(0.3)
        
        amount = data.get("l) Amount of valuation", "N/A")
        val_date = data.get("f) Valuation date")
        val_date_str = val_date.strftime("%d %B %Y") if val_date else "N/A"
        
        purpose = data.get("c) Purpose of the valuation", "N/A")
        if len(purpose) > 42:
            purpose = purpose[:39] + "..."
            
        client = data.get("b) Client details", "N/A")
        if len(client) > 42:
            client = client[:39] + "..."
            
        property_id = data.get("d) Identification of the property", "N/A")
        if len(property_id) > 42:
            property_id = property_id[:39] + "..."
            
        basis = data.get("e) Basis of value adopted", "N/A")
        if len(basis) > 42:
            basis = basis[:39] + "..."

        metrics = [
            ("ASSESSED MARKET VALUE", f"LKR {amount}", "EFFECTIVE VALUATION DATE", val_date_str),
            ("CLIENT / INTENDED USER", client, "VALUATION PURPOSE", purpose),
            ("PROPERTY IDENTIFICATION", property_id, "BASIS OF VALUE ADOPTED", basis)
        ]
        
        # Section title
        self.set_font("Arial", "B", 11)
        self.set_text_color(*MAROON)
        self.cell(CONTENT_W, 8, "EXECUTIVE VALUATION SUMMARY", ln=True)
        
        self.set_draw_color(*GOLD)
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y() + 1, PAGE_W - MARGIN, self.get_y() + 1)
        self.ln(4)
        
        cell_w = CONTENT_W / 2
        for title1, val1, title2, val2 in metrics:
            y_start = self.get_y()
            
            # Left box
            self.set_draw_color(*LIGHT_GRAY)
            self.set_fill_color(*CARD_BG)
            self.rect(MARGIN, y_start, cell_w - 2, 14, "DF")
            self.set_xy(MARGIN + 3, y_start + 1.8)
            self.set_font("Arial", "B", 7.5)
            self.set_text_color(*MID_GRAY)
            self.cell(cell_w - 8, 4, title1, ln=True)
            self.set_x(MARGIN + 3)
            self.set_font("Arial", "B", 9)
            self.set_text_color(*DARK_GRAY)
            self.cell(cell_w - 8, 5, self._safe_str(val1), ln=True)
            
            # Right box
            self.rect(MARGIN + cell_w + 2, y_start, cell_w - 2, 14, "DF")
            self.set_xy(MARGIN + cell_w + 5, y_start + 1.8)
            self.set_font("Arial", "B", 7.5)
            self.set_text_color(*MID_GRAY)
            self.cell(cell_w - 8, 4, title2, ln=True)
            self.set_x(MARGIN + cell_w + 5)
            self.set_font("Arial", "B", 9)
            self.set_text_color(*DARK_GRAY)
            self.cell(cell_w - 8, 5, self._safe_str(val2), ln=True)
            
            self.set_y(y_start + 16)
        self.ln(2)

    def embed_standardized_image(self, src_path: str, caption: str = "", force_orientation: str = None) -> bool:
        """
        Embeds an image into a STATIC, PREDEFINED container.
        Orientation is auto-detected (Landscape vs Portrait).
        Landscape container: Fixed 140mm x 80mm
        Portrait container: Fixed 90mm x 110mm
        The container height on page is FIXED. Uploaded image resolution/ratio 
        CANNOT alter the layout pagination.
        """
        if not os.path.exists(src_path):
            self.set_font("Arial", "I", 8.5)
            self.set_text_color(*MID_GRAY)
            self.cell(CONTENT_W, 6, f"[Photograph File Missing: {caption}]", ln=True, align="C")
            self.ln(2)
            return False

        try:
            from PIL import Image as PILImage, ImageOps
            with PILImage.open(src_path) as im:
                im = ImageOps.exif_transpose(im)
                w_px, h_px = im.size
                
            orientation = force_orientation or ("landscape" if w_px >= h_px else "portrait")
            
            if orientation == "landscape":
                target_w = 140.0
                target_h = 80.0
            else: # portrait
                target_w = 90.0
                target_h = 110.0

            # Ensure space for container + caption + spacing
            self.ensure_space(target_h + 12)
            
            # Standardize image on disk to fit target container exactly without distortion
            cache_dir = "images/cache_standard"
            os.makedirs(cache_dir, exist_ok=True)
            base_name = os.path.basename(src_path)
            std_path = os.path.join(cache_dir, f"std_{orientation}_{base_name}")
            
            standardize_image_for_container(src_path, std_path, target_w, target_h)

            x = MARGIN + (CONTENT_W - target_w) / 2
            curr_y = self.get_y()
            
            # Subtle outer shadow box border
            self.set_draw_color(*LIGHT_GRAY)
            self.set_fill_color(*WHITE)
            self.set_line_width(0.3)
            self.rect(x - 0.8, curr_y - 0.8, target_w + 1.6, target_h + 1.6, "DF")

            # Insert image
            self.image(std_path, x=x, y=curr_y, w=target_w, h=target_h)
            
            # Advance Y precisely by container height
            self.set_y(curr_y + target_h + 2)
            
            if caption:
                self.set_font("Arial", "I", 8)
                self.set_text_color(*MID_GRAY)
                self.cell(CONTENT_W, 4.5, self._safe_str(caption), ln=True, align="C")
                self.ln(2)
            else:
                self.ln(3)
                
            return True
        except Exception as e:
            self.set_font("Arial", "I", 8.5)
            self.set_text_color(*MID_GRAY)
            self.cell(CONTENT_W, 6, f"[Image Render Failure: {caption} - {e}]", ln=True, align="C")
            self.ln(2)
            return False

    def embed_dual_side_by_side_images(self, img_info1: tuple, img_info2: tuple) -> bool:
        """
        Embeds two images side-by-side in fixed twin containers (85mm x 95mm each).
        """
        target_w = 85.0
        target_h = 95.0
        gap = CONTENT_W - (2 * target_w) # 10mm gap
        
        self.ensure_space(target_h + 12)
        curr_y = self.get_y()
        cache_dir = "images/cache_standard"
        os.makedirs(cache_dir, exist_ok=True)

        for i, (path, caption) in enumerate([img_info1, img_info2]):
            x = MARGIN + i * (target_w + gap)
            if os.path.exists(path):
                base_name = os.path.basename(path)
                std_path = os.path.join(cache_dir, f"twin_{i}_{base_name}")
                standardize_image_for_container(path, std_path, target_w, target_h)

                self.set_draw_color(*LIGHT_GRAY)
                self.set_fill_color(*WHITE)
                self.set_line_width(0.3)
                self.rect(x - 0.8, curr_y - 0.8, target_w + 1.6, target_h + 1.6, "DF")
                self.image(std_path, x=x, y=curr_y, w=target_w, h=target_h)
            else:
                self.set_draw_color(*LIGHT_GRAY)
                self.set_fill_color(*CARD_BG)
                self.rect(x, curr_y, target_w, target_h, "DF")

        self.set_y(curr_y + target_h + 2)
        
        # Dual Captions
        self.set_font("Arial", "I", 8)
        self.set_text_color(*MID_GRAY)
        self.set_x(MARGIN)
        self.cell(target_w, 4.5, self._safe_str(img_info1[1]), ln=False, align="C")
        self.set_x(MARGIN + target_w + gap)
        self.cell(target_w, 4.5, self._safe_str(img_info2[1]), ln=True, align="C")
        self.ln(3)
        return True

    def summary_box(self, text: str):
        lines_est = max(6, len(text) // 85 + 2)
        box_h = lines_est * 5.2 + 14
        
        self.ensure_space(min(box_h, 120))
        box_y = self.get_y()
            
        # Draw background and left maroon border
        self.set_fill_color(*CREAM_BG)
        self.set_draw_color(*MAROON)
        self.set_line_width(0.4)
        self.rect(MARGIN, box_y, CONTENT_W, box_h, "DF")
        
        # Left maroon bar
        self.set_fill_color(*MAROON)
        self.rect(MARGIN, box_y, 4.5, box_h, "F")
        
        self.set_xy(MARGIN + 8, box_y + 4)
        self.set_text_color(*MAROON)
        self.set_font("Arial", "B", 10)
        self.cell(0, 5, "AI-Generated Property Summary (Google Gemini Synthesis)", ln=True)
        self.ln(1)
        self.set_x(MARGIN + 8)
        self.set_text_color(*DARK_GRAY)
        self.set_font("Arial", "", 9)
        self.multi_cell(CONTENT_W - 12, 5.0, self._safe_str(text))
        
        self.set_y(box_y + box_h + 4)

    def section_certificate(self, valuer: str, client: str, amount: str, val_date: str, rep_date: str):
        self.ensure_space(82)
            
        self.set_fill_color(*CARD_BG)
        self.set_draw_color(*MAROON)
        self.set_line_width(0.6)
        
        words = amount_to_words(amount)
        
        box_y = self.get_y() + 2
        box_h = 76
        self.rect(MARGIN, box_y, CONTENT_W, box_h, "DF")
        
        # Double gold line interior border
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.rect(MARGIN + 1.8, box_y + 1.8, CONTENT_W - 3.6, box_h - 3.6, "D")
        
        # Certificate Header
        self.set_xy(MARGIN + 5, box_y + 4)
        self.set_font("Arial", "B", 13)
        self.set_text_color(*MAROON)
        self.cell(CONTENT_W - 10, 6, "OFFICIAL VALUATION CERTIFICATE", ln=True, align="C")
        
        self.set_x(MARGIN + 5)
        self.set_font("Arial", "I", 8.5)
        self.set_text_color(*MID_GRAY)
        self.cell(CONTENT_W - 10, 4, "Formal Declaration & Certification of Assessed Market Value", ln=True, align="C")
        self.ln(3)
        
        # Declaration paragraph
        self.set_x(MARGIN + 8)
        self.set_font("Arial", "", 9.5)
        self.set_text_color(*DARK_GRAY)
        stmt = (
            f"I hereby certify that, having physically inspected the subject asset and conducted all necessary "
            f"local market investigations, the estimated Market Value of the specified property interest as of "
            f"the effective valuation date ({val_date}) is formally assessed as:"
        )
        self.multi_cell(CONTENT_W - 16, 4.6, self._safe_str(stmt))
        self.ln(2.5)
        
        # Bold figures block
        self.set_x(MARGIN + 8)
        self.set_font("Arial", "B", 11.5)
        self.set_text_color(*MAROON)
        self.cell(CONTENT_W - 16, 5, f"VALUATION IN FIGURES: LKR {self._safe_str(amount)}", ln=True, align="C")
        
        # Bold words block
        self.set_x(MARGIN + 8)
        self.set_font("Arial", "BI", 9)
        self.set_text_color(*DARK_GRAY)
        self.multi_cell(CONTENT_W - 16, 4.5, self._safe_str(f"VALUATION IN WORDS: {words}"), align="C")
        self.ln(4)
        
        # Signature boxes
        y_sig = self.get_y()
        self.set_xy(MARGIN + 10, y_sig)
        self.set_font("Arial", "B", 8.5)
        self.set_text_color(*DARK_GRAY)
        self.cell(CONTENT_W / 2 - 10, 4, "VALUER / SURVEYOR:", ln=False)
        self.cell(CONTENT_W / 2 - 10, 4, "CHARTERED SURVEYOR SIGN-OFF:", ln=True)
        
        self.set_x(MARGIN + 10)
        self.set_font("Arial", "", 8.5)
        self.set_text_color(*MID_GRAY)
        self.cell(CONTENT_W / 2 - 10, 4, self._safe_str(valuer), ln=False)
        
        self.set_x(MARGIN + CONTENT_W / 2 + 10)
        self.cell(CONTENT_W / 2 - 20, 4, "_____________________________", ln=True)
        
        self.set_x(MARGIN + 10)
        self.cell(CONTENT_W / 2 - 10, 4, "Chartered Valuation Surveyor", ln=False)
        self.set_x(MARGIN + CONTENT_W / 2 + 10)
        self.set_font("Arial", "I", 7.5)
        self.cell(CONTENT_W / 2 - 20, 4, f"Official Stamp & Date: {rep_date}", ln=True)
        
        self.set_y(box_y + box_h + 4)


class PDFGenerator:
    LOGO_URL = "https://www.sjp.ac.lk/wp-content/uploads/2020/10/usjp-logo-300x300.png"

    def generate(self, data: dict, api_key: str, ai_summary: str = "") -> str:
        pdf = PDFReport()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=18)
        
        if not ai_summary or "unavailable" in ai_summary or "Rate limited" in ai_summary:
            ai_summary = AISummaryGenerator.generate(data, api_key)
            
        self._build_cover_page(pdf, data)
        
        pdf.add_page()
        pdf.render_key_metrics(data)
        self._build_report_sections(pdf, data, ai_summary)
        
        os.makedirs("generated_reports", exist_ok=True)
        report_id = datetime.now().strftime("PROPIQ-%Y%m%d-%H%M%S")
        filename = f"generated_reports/valuation_report_{report_id}.pdf"
        pdf.output(filename)
        return filename

    def _build_cover_page(self, pdf: PDFReport, data: dict):
        pdf.add_page()
        
        # 1. Maroon Header Block
        pdf.set_fill_color(*MAROON)
        pdf.rect(0, 0, PAGE_W, 60, "F")
        
        # 2. USJP Logo
        logo_path = "images/usjp_logo.png"
        if os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=PAGE_W - MARGIN - 28, y=10, w=28)
            except Exception:
                pass
            
        # 3. Header text
        pdf.set_xy(MARGIN, 15)
        pdf.set_font("Arial", "B", 24)
        pdf.set_text_color(*GOLD)
        pdf.cell(0, 10, "PROPIQ", ln=True)
        pdf.set_x(MARGIN)
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*WHITE)
        pdf.cell(0, 6, "PROPERTY VALUATION APPRAISAL REPORT", ln=True)
        pdf.set_x(MARGIN)
        pdf.set_font("Arial", "", 8.5)
        pdf.set_text_color(226, 232, 240)
        pdf.cell(0, 5, "Department of Estate Management & Valuation | University of Sri Jayewardenepura", ln=True)
        
        # 4. Gold line divider
        pdf.set_fill_color(*GOLD)
        pdf.rect(0, 60, PAGE_W, 2.5, "F")
        
        pdf.ln(16)
        
        # 5. Valuation Amount Callout Card
        amount = data.get("l) Amount of valuation", "")
        if amount:
            pdf.set_fill_color(*CREAM_BG)
            pdf.set_draw_color(*MAROON)
            pdf.set_line_width(0.4)
            pdf.rect(MARGIN + 10, pdf.get_y(), CONTENT_W - 20, 22, "DF")
            
            y_amt = pdf.get_y() + 4
            pdf.set_xy(MARGIN + 10, y_amt)
            pdf.set_font("Arial", "B", 8)
            pdf.set_text_color(*MID_GRAY)
            pdf.cell(CONTENT_W - 20, 4, "FINAL ASSESSED MARKET VALUE", ln=True, align="C")
            
            pdf.set_x(MARGIN + 10)
            pdf.set_font("Arial", "B", 17)
            pdf.set_text_color(*MAROON)
            pdf.cell(CONTENT_W - 20, 9, f"LKR {pdf._safe_str(amount)}", ln=True, align="C")
            pdf.ln(11)
            
        # 6. Reference and Dates Card
        report_id = datetime.now().strftime("PROPIQ-%Y%m%d-%H%M%S")
        val_date = data.get("f) Valuation date")
        val_date_str = val_date.strftime("%d %B %Y") if val_date else "N/A"
        
        pdf.set_font("Arial", "B", 8.5)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(CONTENT_W / 2, 5, f"REPORT REF: {report_id}", ln=False, align="L")
        pdf.cell(CONTENT_W / 2, 5, f"VALUATION DATE: {val_date_str.upper()}", ln=True, align="R")
        
        pdf.set_draw_color(*LIGHT_GRAY)
        pdf.set_line_width(0.3)
        pdf.line(MARGIN, pdf.get_y() + 1, MARGIN + CONTENT_W, pdf.get_y() + 1)
        pdf.ln(4)
        
        # 7. Metadata blocks (Prepared for / Prepared by)
        pdf.set_fill_color(*CARD_BG)
        pdf.set_draw_color(*LIGHT_GRAY)
        pdf.set_line_width(0.3)
        
        y_pos = pdf.get_y()
        pdf.rect(MARGIN, y_pos, CONTENT_W, 25, "DF")
        
        pdf.set_xy(MARGIN + 5, y_pos + 3)
        pdf.set_font("Arial", "B", 8.5)
        pdf.set_text_color(*MAROON)
        pdf.cell(CONTENT_W / 2 - 5, 5, "PREPARED BY (VALUER)", ln=False)
        pdf.cell(CONTENT_W / 2 - 5, 5, "PREPARED FOR (CLIENT)", ln=True)
        
        pdf.set_x(MARGIN + 5)
        pdf.set_font("Arial", "B", 9.5)
        pdf.set_text_color(*DARK_GRAY)
        valuer = data.get("a) Identification and status of the valuer", "N/A")
        client = data.get("b) Client details", "N/A")
        pdf.cell(CONTENT_W / 2 - 5, 5, pdf._safe_str(valuer)[:42], ln=False)
        pdf.cell(CONTENT_W / 2 - 5, 5, pdf._safe_str(client)[:42], ln=True)
        
        pdf.set_x(MARGIN + 5)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(CONTENT_W / 2 - 5, 4, "Chartered Valuation Surveyor", ln=False)
        pdf.cell(CONTENT_W / 2 - 5, 4, "Applicant / Intended Client", ln=True)
        
        pdf.ln(7)
        
        # 8. Cover Photo Container (Static fixed container)
        images: list[PropertyImage] = data.get("r) Property Images", [])
        if images and images[0].exists():
            pdf.embed_standardized_image(images[0].path, caption="Primary Subject Property Photograph (Cover Photo)")

    def _build_report_sections(self, pdf: PDFReport, data: dict, ai_summary: str = ""):
        # Section 01: Purpose
        pdf.section_heading("01.0  PURPOSE OF VALUATION")
        purpose = data.get("c) Purpose of the valuation", "N/A")
        client = data.get("b) Client details", "N/A")
        purpose_paragraph = (
            f"This professional property valuation report has been commissioned for the primary purpose of assessing "
            f"and declaring the market value of the subject property interest as requested by the client, {client}.\n\n"
            f"The specific scope and intent for which this valuation is conducted is: {purpose}.\n\n"
            f"This report is strictly confidential and has been prepared exclusively for the client and their authorized "
            f"representatives. No third-party liability is accepted for reliance placed on this document outside its declared scope."
        )
        pdf.report_paragraph(purpose_paragraph)
        pdf.divider()

        # Section 02: Date of Inspection
        pdf.section_heading("02.0  DATE OF INSPECTION & EFFECTIVE VALUATION DATE")
        val_date = data.get("f) Valuation date")
        val_date_str = val_date.strftime("%d %B %Y") if val_date else "N/A"
        valuer = data.get("a) Identification and status of the valuer", "N/A")
        inspection_paragraph = (
            f"The subject property was physically inspected on {val_date_str} by the valuer, {valuer}.\n\n"
            f"The physical state of the structures, ground improvements, and prevailing local market conditions as of "
            f"this date form the empirical basis of this valuation. In accordance with International Valuation Standards (IVS), "
            f"the date of physical inspection is adopted as the effective valuation date."
        )
        pdf.report_paragraph(inspection_paragraph)
        pdf.divider()

        # Section 03: Property Identification
        pdf.section_heading("03.0  IDENTIFICATION OF PROPERTY")
        prop_id = data.get("d) Identification of the property", "N/A")
        identification_paragraph = (
            f"The subject property under valuation is legal, physical, and administratively described as follows:\n\n"
            f"{prop_id}\n\n"
            f"This identification has been cross-verified against title deed particulars, surveyor partition plans, and "
            f"local authority assessment records provided by the client."
        )
        pdf.report_paragraph(identification_paragraph)
        pdf.divider()

        # Section 04: Nature of Property
        pdf.section_heading("04.0  NATURE AND TENURE OF PROPERTY")
        nature = data.get("g) Nature of the property", "N/A")
        nature_paragraph = (
            f"The tenure, legal interest, and operational occupancy status of the property under valuation are described below:\n\n"
            f"{nature}\n\n"
            f"Unless specifically qualified in this report, it is assumed that the asset is held under an unencumbered Freehold interest, "
            f"free from restrictive covenants, unauthorized encroachments, or legal disputes."
        )
        pdf.report_paragraph(nature_paragraph)
        pdf.divider()

        # Section 05: Site Profile
        pdf.section_heading("05.0  SITE PROFILE & STRUCTURAL AUDIT")
        pdf.sub_heading("05.1  Land Profile & Topography")
        land_profile = data.get("h) Site profile", "N/A")
        land_paragraph = (
            f"The site characteristics, terrain configuration, soil stability, and boundaries are detailed as follows:\n\n"
            f"{land_profile}"
        )
        pdf.report_paragraph(land_paragraph)
        
        pdf.sub_heading("05.2  Building & Structural Inspection")
        parts = data.get("q) Selected Property Parts", [])
        if parts:
            parts_str = ", ".join(parts)
            building_paragraph = (
                f"A physical structural inspection of the main building components was conducted. Inspected areas include: {parts_str}.\n\n"
                f"The masonry, roof framing, floor finishes, and service utility installations within the inspected sections "
                f"were found to be in fair to good operational condition suitable for standard occupancy."
            )
        else:
            building_paragraph = (
                "The building structure was visually inspected from the exterior and main access points. No detailed internal "
                "section breakdown was requested."
            )
        pdf.report_paragraph(building_paragraph)

        # Section 05.3: Photographs Grid (Static Container standardization)
        images: list[PropertyImage] = data.get("r) Property Images", [])
        sub_images = [img for img in images[1:] if img.exists()] if len(images) > 1 else []
        
        if sub_images:
            pdf.sub_heading("05.3  Photographic Documentation of Inspected Sections")
            pdf.guidance_text("All property photographs are rendered in standardized, predefined containers to ensure stable report pagination.")
            
            i = 0
            while i < len(sub_images):
                # If 2 portrait images in a row, place side by side
                info1 = sub_images[i].get_info()
                if i + 1 < len(sub_images):
                    info2 = sub_images[i+1].get_info()
                    if info1["orientation"] == "portrait" and info2["orientation"] == "portrait":
                        pdf.embed_dual_side_by_side_images(
                            (sub_images[i].path, f"Inspected: {sub_images[i].part}"),
                            (sub_images[i+1].path, f"Inspected: {sub_images[i+1].part}")
                        )
                        i += 2
                        continue
                
                # Otherwise embed single standardized image container
                pdf.embed_standardized_image(
                    sub_images[i].path, 
                    caption=f"Inspected Property Section: {sub_images[i].part}"
                )
                i += 1

        self._insert_location_map(pdf, data)
        pdf.divider()

        # Section 06: Market Evidence
        pdf.section_heading("06.0  EVIDENCE OF MARKET VALUES")
        evidence = data.get("i) Market value evidence", "N/A")
        evidence_paragraph = (
            f"In establishing market value, comparable land transactions, land registry sales, and local real estate broker "
            f"rates were analyzed. Empirical market evidence gathered in the subject neighborhood includes:\n\n"
            f"{evidence}\n\n"
            f"The comparative rate analysis per perch and depreciated replacement cost per square foot establish the baseline valuation metrics."
        )
        pdf.report_paragraph(evidence_paragraph)
        pdf.divider()

        # Section 07: Assumptions & Reservations
        pdf.section_heading("07.0  ASSUMPTIONS AND SPECIAL RESERVATIONS")
        assumptions = data.get("j) Assumptions and reservations", "N/A")
        assumptions_paragraph = (
            f"This valuation report has been prepared subject to the following standard assumptions and limiting reservations:\n\n"
            f"{assumptions}\n\n"
            f"These assumptions are adopted on the premise that no unstated legal liabilities, environmental contamination, or "
            f"hidden structural defects exist that would adversely affect the market value."
        )
        pdf.report_paragraph(assumptions_paragraph)
        pdf.divider()

        # Section 08: Basis
        pdf.section_heading("08.0  BASIS OF VALUATION")
        basis = data.get("e) Basis of value adopted", "N/A")
        basis_paragraph = (
            f"The valuation has been prepared on the basis of: {basis}.\n\n"
            f"In accordance with International Valuation Standard IVS 104, Market Value is defined as the estimated amount for "
            f"which an asset or liability should exchange on the valuation date between a willing buyer and a willing seller in an "
            f"arm's-length transaction, after proper marketing wherein the parties had each acted knowledgeably, prudently, and without compulsion."
        )
        pdf.report_paragraph(basis_paragraph)
        pdf.divider()

        # Section 09: Valuation Approach
        pdf.section_heading("09.0  VALUATION APPROACH AND REASONING")
        approach = data.get("k) Valuation approach", "N/A")
        approach_paragraph = (
            f"In synthesizing the final value, the surveyor adopted the following appraisal methodology:\n\n"
            f"{approach}\n\n"
            f"The chosen methodology aligns with recognised surveying standards, reflecting the nature of the property and market data availability."
        )
        pdf.report_paragraph(approach_paragraph)
        pdf.divider()

        # Section 10: Official Certificate
        pdf.section_heading("10.0  VALUATION CERTIFICATE")
        valuer       = data.get("a) Identification and status of the valuer", "__________")
        client       = data.get("b) Client details", "__________")
        amount       = data.get("l) Amount of valuation", "__________")
        rep_date     = data.get("m) Date of the valuation report")
        rep_date_str = rep_date.strftime("%d %B %Y") if rep_date else "__________"
        
        pdf.section_certificate(valuer, client, amount, val_date_str, rep_date_str)

        # Section 11: AI Summary (Fresh Page if needed)
        pdf.add_page()
        pdf.section_heading("11.0  PROPERTY SUMMARY")
        pdf.guidance_text(
            "The following narrative summary has been compiled by Google Gemini AI based on the full valuation survey parameters entered above."
        )
        pdf.ln(2)
        if ai_summary:
            pdf.summary_box(ai_summary)
        else:
            pdf.user_value("No AI summary available.")

        pdf.ln(4)
        pdf.set_font("Arial", "B", 8.5)
        pdf.set_text_color(*MAROON)
        pdf.cell(CONTENT_W, 6,
                 f"Official Document Timestamp: {datetime.now().strftime('%d %B %Y  %H:%M:%S')}",
                 ln=True, align="R")

    def _insert_location_map(self, pdf: PDFReport, data: dict):
        try:
            from PIL import Image as PILImage, ImageDraw
        except ImportError:
            return

        lat     = data.get("Latitude")
        lon     = data.get("Longitude")
        address = data.get("Location Address", "")
        if not lat or not lon:
            return

        pdf.sub_heading("05.4  Property Geolocation Map")
        pdf.set_text_color(*MID_GRAY)
        pdf.set_font("Arial", "", 8.5)
        if address:
            pdf.multi_cell(CONTENT_W, 4.5, f"Pinned Location Address: {pdf._safe_str(address)}")
        pdf.multi_cell(CONTENT_W, 4.5, f"Coordinates: {lat:.6f} N,  {lon:.6f} E")
        pdf.ln(2)

        zoom      = 15
        tile_size = 256
        grid      = 3

        def deg2tile(la, lo, z):
            n  = 2 ** z
            tx = int((lo + 180.0) / 360.0 * n)
            ty = int((1.0 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2.0 * n)
            return tx, ty

        def coord2px(la, lo, z, ox, oy):
            n  = 2 ** z
            px = (lo + 180.0) / 360.0 * n * tile_size - ox * tile_size
            py = (1.0 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2.0 * n * tile_size - oy * tile_size
            return int(px), int(py)

        cx, cy = deg2tile(lat, lon, zoom)
        half   = grid // 2
        canvas = PILImage.new("RGB", (tile_size * grid, tile_size * grid), (220, 220, 220))
        hdrs   = {"User-Agent": "PROPIQ-ValuationApp/1.0"}

        for row in range(grid):
            for col in range(grid):
                url = f"https://tile.openstreetmap.org/{zoom}/{cx-half+col}/{cy-half+row}.png"
                try:
                    r = requests.get(url, headers=hdrs, timeout=10)
                    if r.status_code == 200:
                        tile = PILImage.open(io.BytesIO(r.content)).convert("RGB")
                        canvas.paste(tile, (col * tile_size, row * tile_size))
                except Exception:
                    pass

        px, py = coord2px(lat, lon, zoom, cx - half, cy - half)
        draw   = ImageDraw.Draw(canvas)
        for radius, colour in [(14, MAROON), (10, (220, 30, 30)), (4, WHITE)]:
            draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=colour)
        draw.rectangle([0, 0, canvas.width-1, canvas.height-1], outline=MAROON, width=4)

        os.makedirs("images", exist_ok=True)
        map_path = "images/location_map_pdf.png"
        canvas.save(map_path)

        try:
            # Embed location map in standardized landscape container
            pdf.embed_standardized_image(map_path, caption="Property Geolocation Pin Map (OpenStreetMap)", force_orientation="landscape")
        except Exception as e:
            pdf.guidance_text(f"Map graphic error: {e}")
        finally:
            try:
                os.remove(map_path)
            except Exception:
                pass

    def cleanup(self, pdf_path: str, images: list[PropertyImage]):
        for img in images:
            img.remove()