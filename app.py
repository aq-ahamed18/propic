import streamlit as st
import base64
import os
from datetime import datetime

# Important: Must set page configuration at the very top!
st.set_page_config(page_title="PROPIQ | Valuation Report", page_icon="📄", layout="wide")

# Importing our newly created modules
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #f8fafc;
        }
        
        main .block-container {
            padding-top: 1.5rem !important; 
            margin-top: 0rem !important;
            max-width: 1200px;
        }
        
        /* Custom Header styling */
        .header {
            background: linear-gradient(135deg, #7A0016, #b31b34);
            padding: 30px 20px; 
            border-radius: 16px;
            text-align: center; 
            box-shadow: 0 8px 24px rgba(122, 0, 22, 0.15);
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }
        
        .header::after {
            content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3z' fill='%23ffffff' fill-opacity='0.04' fill-rule='evenodd'/%3E%3C/svg%3E");
        }
        
        .header h1 {
            color: #ffffff; 
            font-size: 40px; 
            font-weight: 800; 
            margin: 0; 
            letter-spacing: -1.5px;
            position: relative; z-index: 1;
        }
        
        .header h4 {
            color: #ffdca8; 
            font-weight: 500; 
            margin: 8px 0 0; 
            font-size: 16px;
            letter-spacing: 0.2px;
            position: relative; z-index: 1;
        }
       
        /* Card styling */
        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 4px 18px rgba(0,0,0,0.03);
            border: 1px solid rgba(0,0,0,0.04);
            margin-bottom: 25px;
        }
        
        .section-title {
            color: #7A0016; 
            font-size: 22px; 
            font-weight: 700; 
            margin-bottom: 20px;
            letter-spacing: -0.5px;
            border-bottom: 2px solid #f1f5f9;
            padding-bottom: 8px;
        }
        
        label {
            color: #475569 !important; 
            font-weight: 600 !important;
            font-size: 13.5px !important;
        }
        
        .stTextInput input, .stTextArea textarea, .stDateInput input {
            background-color: #f8fafc; 
            border: 1px solid #e2e8f0;
            border-radius: 8px; 
            color: #0f172a;
            padding: 0.5rem 0.75rem;
            transition: all 0.2s ease;
        }
        
        .stTextInput input:focus, .stTextArea textarea:focus, .stDateInput input:focus {
            border-color: #7A0016; 
            box-shadow: 0 0 0 3px rgba(122, 0, 22, 0.12);
            background-color: #ffffff;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #7A0016, #9b0c24); 
            color: white;
            border-radius: 8px; 
            font-weight: 600;
            padding: 0.55rem 1.4rem; 
            border: none;
            transition: all 0.2s ease;
            box-shadow: 0 4px 10px rgba(122, 0, 22, 0.15);
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #8c0a20, #b01b34); 
            color: white; 
            transform: translateY(-1px);
            box-shadow: 0 6px 14px rgba(122, 0, 22, 0.22);
        }
        
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(122, 0, 22, 0.15), transparent);
            margin: 25px 0;
        }
        
        .footer {
            text-align: center; 
            color: #94a3b8; 
            font-size: 13.5px; 
            margin-top: 30px;
            padding-bottom: 20px;
        }
        
        /* Premium custom Streamlit Tabs Styling */
        div.stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 20px;
        }
        div.stTabs [data-baseweb="tab"] {
            height: 48px;
            white-space: pre-wrap;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-bottom: none;
            border-radius: 8px 8px 0px 0px;
            color: #475569;
            font-weight: 600;
            font-size: 14px;
            padding: 8px 22px;
            transition: all 0.25s ease;
        }
        div.stTabs [data-baseweb="tab"]:hover {
            color: #7A0016;
            background-color: #f8fafc;
            border-color: #cbd5e1;
        }
        div.stTabs [aria-selected="true"] {
            background-color: #7A0016 !important;
            color: #ffffff !important;
            border-color: #7A0016 !important;
            box-shadow: 0 -4px 12px rgba(122, 0, 22, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        st.markdown("""
        <div class="header">
            <h1>PROPIQ</h1>
            <h4>Professional Property Valuation Report Engine — University of Sri Jayewardenepura</h4>
        </div>
        """, unsafe_allow_html=True)

    @classmethod
    def render_sidebar(cls):
        with st.sidebar:
            st.image(cls.LOGO_URL, width=110)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if SessionManager.get("logged_in"):
                st.markdown(f"👤 **Role: Chartered Surveyor**<br>**Active User: {SessionManager.get('username')}**", unsafe_allow_html=True)
                st.divider()
                if st.button("🚪 Logout Account", use_container_width=True):
                    SessionManager.logout()
            else:
                st.markdown("🔒 Please login to access the valuation database.")

    @staticmethod
    def render_footer():
        st.markdown("""
        <hr>
        <div class="footer">© 2026 PROPIQ | Department of Estate Management & Valuation | University of Sri Jayewardenepura</div>
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
        st.markdown(f"<h3 style='color:#7A0016; font-weight: 800; letter-spacing: -0.5px;'>Welcome, {username}! 👋</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6b7280; font-size: 15px; margin-top: -10px; margin-bottom: 25px;'>Compile detailed valuation reports, manage saved projects, and converse with the survey assistant.</p>", unsafe_allow_html=True)
        
        # Render Navigation and Settings in sidebar to ensure true lazy-loading of tabs
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            active_tab = st.radio(
                "Go to Workspace:",
                ["📁 Saved Reports", "✍️ Generate New Report", "💬 PropIQ AI Chat Assistant"],
                index=1  # Default to Generate New Report
            )
            st.divider()
            
            st.markdown("### ⚙️ Workspace Settings")
            api_key = self.api_widget.render()
            st.divider()

        # Conditionally render ONLY the active area for true lazy-loading
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
            st.info("💡 No reports have been generated yet. Head over to the 'Generate New Report' tab to create your first valuation report!")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Sort by report timestamp in filename (PROPIQ-YYYYMMDD-HHMMSS.pdf)
        def get_report_time(fname):
            try:
                ts = fname.split("PROPIQ-")[1].split(".pdf")[0]
                return datetime.strptime(ts, "%Y%m%d-%H%M%S")
            except:
                return datetime.fromtimestamp(os.path.getmtime(os.path.join("generated_reports", fname)))

        files = sorted(files, key=get_report_time, reverse=True)

        st.markdown(
            f"<span style='color:#6b7280; font-size: 13.5px;'>Below is the registry of reports successfully saved in your project folder (`generated_reports/`):</span>",
            unsafe_allow_html=True
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        for f in files:
            filepath = os.path.join("generated_reports", f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            try:
                ts = f.split("PROPIQ-")[1].split(".pdf")[0]
                pretty_time = datetime.strptime(ts, "%Y%m%d-%H%M%S").strftime("%b %d, %Y at %I:%M %p")
            except:
                pretty_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%b %d, %Y at %I:%M %p")

            col_inf, col_act = st.columns([3, 1])
            with col_inf:
                st.markdown(
                    f"📄 **Valuation Report PDF** (`{f}`)<br>"
                    f"<span style='color:#6b7280; font-size: 12.5px;'>Created: {pretty_time} &nbsp;|&nbsp; File Size: {size_mb:.2f} MB</span>",
                    unsafe_allow_html=True
                )
            with col_act:
                col_v, col_d, col_rm = st.columns(3)
                with col_v:
                    if st.button("👁️", key=f"view_{f}", help="Open Preview Panel"):
                        st.session_state.preview_report = filepath
                with col_d:
                    with open(filepath, "rb") as rf:
                        st.download_button(
                            label="⬇️",
                            data=rf.read(),
                            file_name=f,
                            mime="application/pdf",
                            key=f"download_{f}",
                            help="Download PDF file"
                        )
                with col_rm:
                    if st.button("🗑️", key=f"delete_{f}", help="Delete Permanently"):
                        try:
                            os.remove(filepath)
                            if "preview_report" in st.session_state and st.session_state.preview_report == filepath:
                                del st.session_state.preview_report
                            st.success(f"Removed {f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            st.divider()

        # Embedded viewer inside dashboard page
        if "preview_report" in st.session_state and os.path.exists(st.session_state.preview_report):
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            st.markdown(f"##### 📑 Previewing: `{os.path.basename(st.session_state.preview_report)}`")
            with open(st.session_state.preview_report, "rb") as pdf_file:
                b64_data = base64.b64encode(pdf_file.read()).decode("utf-8")
            
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_data}" '
                f'width="100%" height="780" style="border: 1px solid #cbd5e1; border-radius: 8px;"></iframe>',
                unsafe_allow_html=True
            )
            
            if st.button("❌ Close Live Preview", use_container_width=True):
                del st.session_state.preview_report
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_valuation_form(self, api_key: str):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">✍️ Property Valuation Appraisal Form</div>', unsafe_allow_html=True)
        
        fields = self.form.render()

        st.markdown("---")
        # Caching Panel for AI Summary
        st.markdown("##### ✨ Google Gemini AI Property Summary")
        sum_col1, sum_col2 = st.columns([3, 1])
        with sum_col1:
            if st.session_state.current_ai_summary:
                with st.expander("👁️ View Cached AI Property Summary (Ready)", expanded=False):
                    st.info(st.session_state.current_ai_summary)
            else:
                st.warning("⚠️ **No AI Summary cached yet.** It will be generated automatically when you compile the report, or you can generate it now to preview.")
        with sum_col2:
            btn_lbl = "🔄 Regenerate Summary" if st.session_state.current_ai_summary else "✨ Generate Summary"
            if st.button(btn_lbl, use_container_width=True):
                val_name = fields.get("a) Identification and status of the valuer")
                client_name = fields.get("b) Client details")
                if not api_key or len(api_key) < 10:
                    st.error("⚠️ Enter Gemini API key first.")
                elif not val_name or not val_name.strip() or not client_name or not client_name.strip():
                    st.error("⚠️ Fill in Valuer & Client details in Step 1 first.")
                else:
                    with st.spinner("Requesting AI Summary from Gemini..."):
                        from ai_locationAPI import AISummaryGenerator
                        summary = AISummaryGenerator.generate(fields, api_key)
                        st.session_state.current_ai_summary = summary
                        st.success("AI Summary Cached!")
                        st.rerun()

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("📄 Compile & Save Valuation Report", use_container_width=True):
            # Check validations
            val_name = fields.get("a) Identification and status of the valuer")
            client_name = fields.get("b) Client details")
            
            if not api_key or len(api_key) < 10:
                st.error("⚠️ **API Key Required**: Please enter a valid Google Gemini API key in the sidebar configuration to proceed.")
            elif not val_name or not val_name.strip():
                st.error("⚠️ **Validation Error**: Please fill in the Valuer credentials in Step 1.")
            elif not client_name or not client_name.strip():
                st.error("⚠️ **Validation Error**: Please fill in the Client name in Step 1.")
            else:
                self._handle_pdf_generation(fields, api_key)
        st.markdown("</div>", unsafe_allow_html=True)

    def _handle_pdf_generation(self, fields: dict, api_key: str):
        # Retrieve cached summary or compile fresh if empty
        summary = st.session_state.current_ai_summary
        if not summary or "unavailable" in summary or "Rate limited" in summary:
            with st.spinner("✨ Synthesizing survey data and generating Gemini AI summary..."):
                from ai_locationAPI import AISummaryGenerator
                summary = AISummaryGenerator.generate(fields, api_key)
                st.session_state.current_ai_summary = summary

        with st.spinner("✨ Writing report details and compiling PDF report..."):
            pdf_path = self.pdf_generator.generate(fields, api_key, ai_summary=summary)

        st.success(f"🎉 Valuation Report successfully compiled and saved in `{pdf_path}`!")
        
        # Set as current preview
        st.session_state.preview_report = pdf_path
        
        # Perform image uploads cleanup
        images: list[PropertyImage] = fields.get("r) Property Images", [])
        self.pdf_generator.cleanup(pdf_path, images)
        
        # Rerun to navigate and open preview
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