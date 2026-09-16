import streamlit as st
import requests
from login import SessionManager

class AIChatbot:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    SYSTEM_PROMPT = (
        "You are PropIQ AI Assistant, an expert Chartered Valuation Surveyor and AI advisor built for the Department of Estate Management & Valuation at the University of Sri Jayewardenepura. "
        "Your role is to assist valuers, students, and clients in understanding real estate valuation concepts, writing professional appraisal clauses, "
        "selecting appropriate valuation methods (e.g., Cost Approach, Income Capitalisation, Direct Market Comparison), drafting standard assumptions and reservations, "
        "and explaining International Valuation Standards (IVS 104, IVS 105, etc.) in a clear, educational, and professional manner. "
        "Maintain a formal, helpful, and technically precise tone. Use clear formatting, bullet points, or markdown tables where appropriate."
    )

    def __init__(self):
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": (
                        "👋 **Welcome to the PropIQ AI Survey Assistant!**\n\n"
                        "I am your dedicated AI advisor for property valuation, surveying standards (IVS), "
                        "report clause drafting, and appraisal methodology. How can I assist your valuation workflow today?"
                    )
                }
            ]

    def render(self, api_key: str):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💬 PropIQ AI Chat Assistant</div>', unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#64748B; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>"
            "Draft valuation clauses, query IVS standards, or explore appraisal methodology with Gemini AI."
            "</p>",
            unsafe_allow_html=True
        )

        if not api_key or len(api_key) < 10:
            st.warning("⚠️ **Google Gemini API Key Required**: Please enter your API key in the sidebar workspace settings to activate the Chat Assistant.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        st.markdown("**💡 Quick Survey Prompts:**")
        col1, col2, col3 = st.columns(3)
        
        prompt_to_send = None
        
        with col1:
            if st.button("📝 Draft Cost Approach Clause", use_container_width=True):
                prompt_to_send = "Write a professional valuation approach description using the Depreciated Replacement Cost Approach for a standard 2-story brick residential dwelling."
        with col2:
            if st.button("⚖️ Explain IVS 104 Market Value", use_container_width=True):
                prompt_to_send = "Explain the formal definition and fundamental requirements of 'Market Value' according to International Valuation Standard (IVS) 104."
        with col3:
            if st.button("🔒 Standard Reservations Checklist", use_container_width=True):
                prompt_to_send = "Provide a comprehensive checklist of standard assumptions, reservations, and limiting conditions for residential land valuation reports."

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        chat_container = st.container(height=460)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_input = st.chat_input("Ask PropIQ Assistant anything about valuation...")
        
        if prompt_to_send:
            user_input = prompt_to_send

        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_input)

            with st.spinner("Synthesizing response with Gemini AI..."):
                response_text = self._call_gemini_api(api_key, st.session_state.chat_messages)
                
            st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    def _call_gemini_api(self, api_key: str, history: list) -> str:
        model = SessionManager.get("google_api_model") or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        formatted_contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            content_text = msg["content"]
            formatted_contents.append({
                "role": role,
                "parts": [{"text": content_text}]
            })

        payload = {
            "contents": formatted_contents,
            "systemInstruction": {
                "parts": [{"text": self.SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }

        import time
        max_retries = 3
        backoff_delay = 2

        for attempt in range(max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue
                    else:
                        try:
                            err_msg = resp.json()["error"]["message"]
                        except Exception:
                            err_msg = resp.text[:200]
                        return f"❌ **AI Chat Rate Limited (429)**: {err_msg}. You can switch AI models in the sidebar workspace settings."

                if resp.status_code in (401, 403):
                    return "❌ **AI Chat Unauthorized**: Invalid or unauthorized Google Gemini API key. Please check your settings."
                
                resp.raise_for_status()
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return raw_text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                return f"❌ **AI Chat Error**: {str(e)}"
