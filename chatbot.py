import streamlit as st
import requests
from login import SessionManager

class AIChatbot:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    SYSTEM_PROMPT = (
        "You are PropIQ Assistant, an expert Chartered Valuation Surveyor and AI advisor built for the University of Sri Jayewardenepura. "
        "Your role is to help students, valuers, and clients understand property valuation, write professional report clauses, "
        "select appropriate valuation methods (e.g., Cost, Income, Market Comparison), draft standard assumptions and reservations, "
        "and explain International Valuation Standards (IVS 104, etc.) in a clear, educational, and professional manner. "
        "Keep your tone formal, helpful, and technically precise. Use clear formatting, bullet points, or tables to explain things."
    )

    def __init__(self):
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {
                    "role": "assistant",
                    "content": (
                        "👋 **Welcome to the PropIQ AI Assistant!**\n\n"
                        "I am here to help you write professional property valuation reports, answer surveying questions, "
                        "and explain valuation standards. How can I assist you today?"
                    )
                }
            ]

    def render(self, api_key: str):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💬 PropIQ AI Chat Assistant</div>', unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#6b7280; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>"
            "Ask questions, draft sections of your report, or explore real estate valuation concepts using AI."
            "</p>",
            unsafe_allow_html=True
        )

        if not api_key or len(api_key) < 10:
            st.warning("⚠️ **Google Gemini API Key is missing.** Please enter your key in the sidebar settings to use the Chat Assistant.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Render Suggestion Chips
        st.markdown("**💡 Quick Suggestions:**")
        col1, col2, col3 = st.columns(3)
        
        prompt_to_send = None
        
        with col1:
            if st.button("📝 Draft a Cost Approach section", use_container_width=True):
                prompt_to_send = "Write a professional valuation approach description using the Cost Approach for a standard 2-story brick residence."
        with col2:
            if st.button("⚖️ Explain Market Value (IVS 104)", use_container_width=True):
                prompt_to_send = "Explain the definition and key elements of 'Market Value' according to International Valuation Standard (IVS) 104."
        with col3:
            if st.button("🔒 Standard assumptions list", use_container_width=True):
                prompt_to_send = "Give me a checklist of standard assumptions and reservations that a valuer should include for residential land valuation."

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Render Chat Messages container
        chat_container = st.container(height=450)
        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Capture user input from chat_input or suggestion chips
        user_input = st.chat_input("Ask PropIQ Assistant anything...")
        
        if prompt_to_send:
            user_input = prompt_to_send

        if user_input:
            # Append user message
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(user_input)

            # Generate response from AI
            with st.spinner("Thinking..."):
                response_text = self._call_gemini_api(api_key, st.session_state.chat_messages)
                
            st.session_state.chat_messages.append({"role": "assistant", "content": response_text})
            # Force refresh to update the container
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    def _call_gemini_api(self, api_key: str, history: list) -> str:
        model = SessionManager.get("google_api_model") or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # Format history for Gemini API (roles: "user" and "model")
        formatted_contents = []
        for msg in history:
            # Skip the initial assistant greeting or format it correctly
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
                "temperature": 0.4,
                "maxOutputTokens": 2048
            }
        }

        import time
        max_retries = 3
        backoff_delay = 2  # initial delay in seconds

        for attempt in range(max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                
                # Check for 429 Rate Limit
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue
                    else:
                        try:
                            err_msg = resp.json()["error"]["message"]
                        except:
                            err_msg = resp.text[:200]
                        return f"❌ **AI Chat rate limited (429)**: {err_msg}"

                if resp.status_code in (401, 403):
                    return "❌ **AI Chat unavailable**: Invalid or unauthorized Google Gemini API key. Please check your settings."
                
                resp.raise_for_status()
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return raw_text
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                return f"❌ **AI Chat Error**: {str(e)}"
