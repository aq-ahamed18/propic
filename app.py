import streamlit as st
import base64
import os
from datetime import datetime

# Important: Must set page configuration at the very top!
st.set_page_config(
    page_title="Prop IQ | Real Estate Valuation Engine — USJP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

from login import SessionManager, AuthPage, UserManager
from form import ValuationForm
from pdfGenarator import PDFGenerator
from ai_locationAPI import APIKeyWidget
from img_prop_handler import PropertyImage
from chatbot import AIChatbot


class UIRenderer:
    LOGO_URL = "https://www.sjp.ac.lk/wp-content/uploads/2020/10/usjp-logo-300x300.png"

    @staticmethod
    def inject_css():
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            color: #0f172a;
        }
        
        .stApp {
            background-color: #f7f1f1 !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(122, 0, 22, 0.07) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(212, 175, 55, 0.08) 0px, transparent 50%),
                radial-gradient(at 50% 30%, rgba(122, 0, 22, 0.03) 0px, transparent 60%) !important;
            background-attachment: fixed !important;
        }

        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        
        main .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 2.5rem !important;
            max-width: 1280px;
        }
        
        /* Custom Institutional Header styling */
        .app-header {
            background: linear-gradient(135deg, #4A000D 0%, #7A0016 45%, #9B111E 100%);
            padding: 28px 36px; 
            border-radius: 16px;
            text-align: left; 
            box-shadow: 0 14px 35px -5px rgba(122, 0, 22, 0.3), 0 6px 15px -4px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
            border-bottom: 4px solid #D4AF37;
        }
        
        .app-header::before {
            content: ''; 
            position: absolute; 
            top: -60%; right: -8%; 
            width: 360px; height: 360px;
            background: radial-gradient(circle, rgba(212,175,55,0.2) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        
        .app-header::after {
            content: ''; 
            position: absolute; 
            bottom: -50%; left: -10%; 
            width: 250px; height: 250px;
            background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        
        .header-title-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 2;
        }
        
        .header-text h1 {
            color: #ffffff; 
            font-size: 34px; 
            font-weight: 800; 
            margin: 0; 
            letter-spacing: -1px;
            line-height: 1.1;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .header-text p {
            color: #fef3c7; 
            font-weight: 500; 
            margin: 8px 0 0; 
            font-size: 15px;
            letter-spacing: 0.1px;
            opacity: 0.95;
        }
        
        .header-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 8px;
        }
        
        .header-badge {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(212, 175, 55, 0.5);
            padding: 7px 16px;
            border-radius: 24px;
            color: #fef3c7;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.18);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: #a7f3d0;
            font-size: 11.5px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
        }
        
        .status-dot {
            width: 7px;
            height: 7px;
            background-color: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
        }
        
        /* Executive Dashboard Stats Row */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-card {
            background: #ffffff;
            border-radius: 14px;
            padding: 18px 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 14px -2px rgba(0,0,0,0.03), 0 2px 6px -1px rgba(0,0,0,0.02);
            display: flex;
            align-items: center;
            gap: 14px;
            transition: all 0.25s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 22px -4px rgba(122, 0, 22, 0.08);
            border-color: #cbd5e1;
        }
        
        .stat-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%);
            color: #7A0016;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            border: 1px solid rgba(122, 0, 22, 0.1);
            flex-shrink: 0;
        }
        
        .stat-content {
            display: flex;
            flex-direction: column;
        }
        
        .stat-label {
            font-size: 11.5px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            font-size: 16px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.2;
            margin-top: 2px;
        }
        
        /* Professional Card styling */
        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 6px 20px -3px rgba(0,0,0,0.04), 0 2px 8px -2px rgba(0,0,0,0.02);
            border: 1px solid #e2e8f0;
            margin-bottom: 24px;
        }
        
        .section-title {
            color: #7A0016; 
            font-size: 21px; 
            font-weight: 800; 
            margin-bottom: 20px;
            letter-spacing: -0.5px;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-title::before {
            content: '';
            display: inline-block;
            width: 5px;
            height: 22px;
            background: linear-gradient(180deg, #D4AF37 0%, #7A0016 100%);
            border-radius: 4px;
        }
        
        label {
            color: #1e293b !important; 
            font-weight: 600 !important;
            font-size: 13.5px !important;
            letter-spacing: -0.1px;
        }
        
        .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox select {
            background-color: #f8fafc !important; 
            border: 1px solid #cbd5e1 !important;
            border-radius: 10px !important; 
            color: #0f172a !important;
            padding: 0.65rem 0.85rem !important;
            font-size: 14px !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) inset !important;
        }
        
        .stTextInput input:hover, .stTextArea textarea:hover, .stDateInput input:hover {
            border-color: #94a3b8 !important;
            background-color: #ffffff !important;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stDateInput input:focus {
            border-color: #7A0016 !important; 
            box-shadow: 0 0 0 3.5px rgba(122, 0, 22, 0.12) !important;
            background-color: #ffffff !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #7A0016 0%, #9B111E 50%, #580010 100%); 
            color: white !important;
            border-radius: 10px; 
            font-weight: 700;
            font-size: 14px;
            padding: 0.65rem 1.4rem; 
            border: none;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 16px rgba(122, 0, 22, 0.2);
            letter-spacing: 0.2px;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #8c0a20 0%, #b01b34 50%, #680012 100%); 
            color: white !important; 
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(122, 0, 22, 0.3);
        }
        
        .stButton > button:active {
            transform: translateY(0);
            box-shadow: 0 4px 10px rgba(122, 0, 22, 0.2);
        }
        
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(122, 0, 22, 0.2), transparent);
            margin: 24px 0;
        }
        
        .footer {
            text-align: center; 
            color: #64748b; 
            font-size: 13px; 
            font-weight: 500;
            margin-top: 30px;
            padding-bottom: 20px;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFFFFF 0%, #F5EAEB 100%) !important;
            border-right: 1px solid rgba(122, 0, 22, 0.12) !important;
            box-shadow: 2px 0 16px rgba(122, 0, 22, 0.04) !important;
        }
        
        /* Custom Streamlit Tabs Styling */
        div.stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 24px;
            padding-bottom: 2px;
        }
        div.stTabs [data-baseweb="tab"] {
            height: 46px;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-bottom: none;
            border-radius: 10px 10px 0px 0px;
            color: #475569;
            font-weight: 600;
            font-size: 14px;
            padding: 10px 22px;
            transition: all 0.25s ease;
        }
        div.stTabs [data-baseweb="tab"]:hover {
            color: #7A0016;
            background-color: #f8fafc;
            border-color: #cbd5e1;
        }
        div.stTabs [aria-selected="true"] {
            background: linear-gradient(180deg, #7A0016 0%, #680012 100%) !important;
            color: #ffffff !important;
            border-color: #7A0016 !important;
            box-shadow: 0 -4px 12px rgba(122, 0, 22, 0.15);
        }
        
        .report-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 14px;
            transition: all 0.25s ease;
        }
        .report-card:hover {
            border-color: #7A0016;
            box-shadow: 0 6px 18px rgba(122, 0, 22, 0.09);
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown("""
        <div class="app-header">
            <div class="header-title-container">
                <div class="header-text">
                    <h1>PROPIQ</h1>
                    <p>Institutional Real Estate Valuation & Property Management System</p>
                </div>
                <div class="header-right">
                    <div class="header-badge">
                        USJP Department of EMV
                    </div>
                    <div class="status-pill">
                        <span class="status-dot"></span> Valuation Engine Active
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    @classmethod
    def render_sidebar(cls):
        with st.sidebar:
            st.markdown(
                f"<div style='text-align: center; padding: 12px 0; background: linear-gradient(180deg, #FFF5F5 0%, #FFFFFF 100%); border-radius: 14px; border: 1px solid #FEE2E2; margin-bottom: 14px;'>"
                f"<img src='{cls.LOGO_URL}' width='95' style='filter: drop-shadow(0 4px 6px rgba(0,0,0,0.08));'><br>"
                f"<span style='font-size: 11px; font-weight: 700; color: #7A0016; letter-spacing: 0.8px; text-transform: uppercase;'>Univ. of Sri Jayewardenepura</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            if SessionManager.get("logged_in"):
                st.markdown(
                    f"<div style='background: linear-gradient(135deg, #F8FAFC 0%, #EDF2F7 100%); border: 1px solid #CBD5E1; border-radius: 12px; padding: 12px 14px; font-size: 13px; color: #1E293B; box-shadow: 0 2px 6px rgba(0,0,0,0.02);'>"
                    f"🛡️ <strong>Chartered Valuation Surveyor</strong><br>"
                    f"<span style='color: #64748B;'>Account:</span> <strong style='color: #7A0016;'>{SessionManager.get('username')}</strong>"
                    f"</div>", 
                    unsafe_allow_html=True
                )
                st.divider()
                if st.button("🚪 Logout Account", use_container_width=True):
                    SessionManager.logout()
            else:
                st.markdown("🔒 **Surveyor Authentication**: Please login to access valuation features.")

    @staticmethod
    def render_footer():
        st.markdown("""
        <hr>
        <div class="footer">
            © 2026 PROPIQ | Department of Estate Management & Valuation | University of Sri Jayewardenepura
        </div>
        """, unsafe_allow_html=True)


class DashboardPage:
    def __init__(self, pdf_generator: PDFGenerator):
        self.form          = ValuationForm()
        self.api_widget    = APIKeyWidget()
        self.pdf_generator = pdf_generator
        self.chatbot       = AIChatbot()
        if "current_ai_summary" not in st.session_state:
            st.session_state.current_ai_summary = ""

    def render(self):
        username = SessionManager.get("username")
        
        # Count saved reports
        os.makedirs("generated_reports", exist_ok=True)
        reports_count = len([f for f in os.listdir("generated_reports") if f.endswith(".pdf")])
        active_model = SessionManager.get("google_api_model") or "gemini-2.5-flash"
        
        st.markdown(
            f"<div style='margin-bottom: 18px;'>"
            f"<h3 style='color:#7A0016; font-weight: 800; letter-spacing: -0.6px; margin:0;'>Welcome back, {username}! 👋</h3>"
            f"<p style='color:#64748b; font-size: 14.5px; margin-top: 4px; margin-bottom: 0;'>Compile standardized valuation reports, manage saved projects, and converse with the survey assistant.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Executive Dashboard Quick Metrics Row
        st.markdown(
            f'<div class="stats-grid">'
            f'  <div class="stat-card">'
            f'      <div class="stat-icon">📄</div>'
            f'      <div class="stat-content">'
            f'          <div class="stat-label">Reports Compiled</div>'
            f'          <div class="stat-value">{reports_count} PDF Documents</div>'
            f'      </div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'      <div class="stat-icon">🛡️</div>'
            f'      <div class="stat-content">'
            f'          <div class="stat-label">Active Surveyor</div>'
            f'          <div class="stat-value">{username}</div>'
            f'      </div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'      <div class="stat-icon">⚡</div>'
            f'      <div class="stat-content">'
            f'          <div class="stat-label">AI Engine</div>'
            f'          <div class="stat-value">{active_model}</div>'
            f'      </div>'
            f'  </div>'
            f'  <div class="stat-card">'
            f'      <div class="stat-icon">📜</div>'
            f'      <div class="stat-content">'
            f'          <div class="stat-label">Valuation Standard</div>'
            f'          <div class="stat-value">IVS 104 Compliant</div>'
            f'      </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        with st.sidebar:
            st.markdown("### 🧭 Workspace Navigation")
            active_tab = st.radio(
                "Select Module:",
                ["✍️ Generate New Report", "📁 Saved Reports", "💬 PropIQ AI Chat Assistant"],
                index=0
            )
            st.divider()
            
            st.markdown("### ⚙️ Workspace Settings")
            api_key = self.api_widget.render()
            st.divider()

        if active_tab == "📁 Saved Reports":
            self._render_reports_history()
        elif active_tab == "✍️ Generate New Report":
            self._render_valuation_form(api_key)
        elif active_tab == "💬 PropIQ AI Chat Assistant":
            self.chatbot.render(api_key)

    def _render_reports_history(self):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📁 Generated Valuation Reports Directory</div>', unsafe_allow_html=True)
        
        os.makedirs("generated_reports", exist_ok=True)
        files = [f for f in os.listdir("generated_reports") if f.endswith(".pdf")]
        
        if not files:
            st.info("💡 **No valuation reports generated yet.** Go to the 'Generate New Report' workspace tab to compile your first report!")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        def get_report_time(fname):
            try:
                ts = fname.split("PROPIQ-")[1].split(".pdf")[0]
                return datetime.strptime(ts, "%Y%m%d-%H%M%S")
            except Exception:
                return datetime.fromtimestamp(os.path.getmtime(os.path.join("generated_reports", fname)))

        files = sorted(files, key=get_report_time, reverse=True)

        st.markdown(
            "<span style='color:#64748b; font-size: 13.5px;'>Saved valuation reports in directory <code>generated_reports/</code>:</span>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        for f in files:
            filepath = os.path.join("generated_reports", f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            try:
                ts = f.split("PROPIQ-")[1].split(".pdf")[0]
                pretty_time = datetime.strptime(ts, "%Y%m%d-%H%M%S").strftime("%b %d, %Y at %I:%M %p")
            except Exception:
                pretty_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%b %d, %Y at %I:%M %p")

            col_inf, col_act = st.columns([3.2, 1.2])
            with col_inf:
                st.markdown(
                    f"📄 **Valuation Report PDF** (`{f}`)<br>"
                    f"<span style='color:#64748b; font-size: 12.5px;'>Created: {pretty_time} &nbsp;|&nbsp; File Size: {size_mb:.2f} MB</span>",
                    unsafe_allow_html=True
                )
            with col_act:
                col_v, col_d, col_rm = st.columns(3)
                with col_v:
                    if st.button("👁️", key=f"view_{f}", help="Open Live PDF Preview"):
                        st.session_state.preview_report = filepath
                with col_d:
                    with open(filepath, "rb") as rf:
                        st.download_button(
                            label="⬇️",
                            data=rf.read(),
                            file_name=f,
                            mime="application/pdf",
                            key=f"download_{f}",
                            help="Download PDF Document"
                        )
                with col_rm:
                    if st.button("🗑️", key=f"delete_{f}", help="Delete Permanently"):
                        try:
                            os.remove(filepath)
                            if "preview_report" in st.session_state and st.session_state.preview_report == filepath:
                                del st.session_state.preview_report
                            st.success(f"Deleted {f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting file: {e}")
            st.divider()

        # High-res embedded PDF previewer modal container
        if "preview_report" in st.session_state and os.path.exists(st.session_state.preview_report):
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown(f"##### 📑 Live Document Preview: `os.path.basename({st.session_state.preview_report})`")
            with open(st.session_state.preview_report, "rb") as pdf_file:
                b64_data = base64.b64encode(pdf_file.read()).decode("utf-8")
            
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_data}" '
                f'width="100%" height="820" style="border: 1px solid #cbd5e1; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);"></iframe>',
                unsafe_allow_html=True
            )
            
            if st.button("❌ Close Live PDF Preview", use_container_width=True):
                del st.session_state.preview_report
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_valuation_form(self, api_key: str):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ Property Valuation Appraisal Form</div>', unsafe_allow_html=True)
        
        fields = self.form.render()

        st.markdown("---")
        st.markdown("##### ✨ Google Gemini AI Property Summary Synthesis")
        sum_col1, sum_col2 = st.columns([3, 1])
        with sum_col1:
            if st.session_state.current_ai_summary:
                with st.expander("👁️ View Synthesized AI Property Summary", expanded=False):
                    st.info(st.session_state.current_ai_summary)
            else:
                st.warning("⚠️ **No AI Summary generated yet.** It will synthesize automatically during report compilation, or click generate to preview now.")
        with sum_col2:
            btn_lbl = "🔄 Regenerate Summary" if st.session_state.current_ai_summary else "✨ Generate Summary"
            if st.button(btn_lbl, use_container_width=True):
                val_name = fields.get("a) Identification and status of the valuer")
                client_name = fields.get("b) Client details")
                if not api_key or len(api_key) < 10:
                    st.error("⚠️ Enter valid Google Gemini API key first.")
                elif not val_name or not val_name.strip() or not client_name or not client_name.strip():
                    st.error("⚠️ Complete Valuer & Client information in Step 1 first.")
                else:
                    with st.spinner("Synthesizing valuation data with Gemini AI..."):
                        from ai_locationAPI import AISummaryGenerator
                        summary = AISummaryGenerator.generate(fields, api_key)
                        st.session_state.current_ai_summary = summary
                        st.success("AI Summary Cached Successfully!")
                        st.rerun()

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("📄 Compile & Generate Valuation Report (PDF)", use_container_width=True):
            val_name = fields.get("a) Identification and status of the valuer")
            client_name = fields.get("b) Client details")
            
            if not api_key or len(api_key) < 10:
                st.error("⚠️ **API Key Required**: Please enter a valid Google Gemini API key in the sidebar configuration.")
            elif not val_name or not val_name.strip():
                st.error("⚠️ **Validation Error**: Please fill in Valuer Name & Status in Step 1.")
            elif not client_name or not client_name.strip():
                st.error("⚠️ **Validation Error**: Please fill in Client Details in Step 1.")
            else:
                self._handle_pdf_generation(fields, api_key)
        st.markdown("</div>", unsafe_allow_html=True)

    def _handle_pdf_generation(self, fields: dict, api_key: str):
        summary = st.session_state.current_ai_summary
        if not summary or "unavailable" in summary or "Rate limited" in summary:
            with st.spinner("✨ Synthesizing survey data with Gemini AI..."):
                from ai_locationAPI import AISummaryGenerator
                summary = AISummaryGenerator.generate(fields, api_key)
                st.session_state.current_ai_summary = summary

        with st.spinner("✨ Writing PDF template layout and standardizing photographs..."):
            pdf_path = self.pdf_generator.generate(fields, api_key, ai_summary=summary)

        st.success(f"🎉 Valuation Report successfully compiled and saved: `{pdf_path}`!")
        st.session_state.preview_report = pdf_path
        
        images: list[PropertyImage] = fields.get("r) Property Images", [])
        self.pdf_generator.cleanup(pdf_path, images)
        st.rerun()


class PropiqApp:
    def __init__(self):
        self.user_manager   = UserManager()
        self.pdf_generator  = PDFGenerator()
        self.ui             = UIRenderer()
        self.auth_page      = AuthPage(self.user_manager)
        self.dashboard_page = DashboardPage(self.pdf_generator)

    def run(self):
        SessionManager.initialise()
        self.ui.inject_css()
        self.ui.render_header()
        self.ui.render_sidebar()
        
        if SessionManager.get("logged_in"):
            self.dashboard_page.render()
        else:
            self.auth_page.render()
            
        self.ui.render_footer()


if __name__ == "__main__":
    app = PropiqApp()
    app.run()