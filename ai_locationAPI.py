import os
import streamlit as st
import requests
from geopy.geocoders import Nominatim
from login import SessionManager

def get_effective_api_key() -> str:
    """
    Returns the active Gemini API key automatically.
    Prioritizes:
    1. User manual input in SessionManager
    2. OS Environment variable (GEMINI_API_KEY or GOOGLE_API_KEY)
    3. Project .env file
    4. Streamlit Secrets (.streamlit/secrets.toml)
    """
    user_key = SessionManager.get("google_api_key")
    if user_key and len(user_key) > 10:
        return user_key

    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key and len(env_key) > 10:
        return env_key

    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if len(val) > 10:
                            return val
        except Exception:
            pass

    try:
        if "GEMINI_API_KEY" in st.secrets and len(st.secrets["GEMINI_API_KEY"]) > 10:
            return st.secrets["GEMINI_API_KEY"]
        if "GOOGLE_API_KEY" in st.secrets and len(st.secrets["GOOGLE_API_KEY"]) > 10:
            return st.secrets["GOOGLE_API_KEY"]
    except Exception:
        pass

    return ""


class APIKeyWidget:
    @staticmethod
    def render() -> str:
        effective_key = get_effective_api_key()
        manual_key = SessionManager.get("google_api_key") or ""
        is_auto = bool(effective_key and not manual_key)

        col1, col2 = st.columns([3.8, 1.2])
        with col1:
            key_input = st.text_input(
                "🔑 Google Gemini API Key",
                value=manual_key if manual_key else (effective_key if is_auto else ""),
                type="password",
                placeholder="Auto-detected or paste key here (AIza...)",
                help="Automatically loaded from .env, OS environment, or secrets.toml. Or paste key manually.",
                key="api_key_input",
            )
            if key_input:
                SessionManager.set("google_api_key", key_input)

        with col2:
            if effective_key and len(effective_key) > 10:
                if is_auto:
                    st.success("⚡ Auto")
                else:
                    st.success("✅ Saved")
            else:
                st.warning("⚠️ No key")
                
        # Model Selection dropdown for quota flexibility
        model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
        saved_model = SessionManager.get("google_api_model") or "gemini-2.5-flash"
        if saved_model not in model_options:
            saved_model = "gemini-2.5-flash"
            
        model_input = st.selectbox(
            "🤖 AI Model Selection",
            model_options,
            index=model_options.index(saved_model),
            help="Switch models if you hit rate limits (429) on the default model.",
            key="api_model_input"
        )
        SessionManager.set("google_api_model", model_input)
        
        return effective_key


class LocationAPI:
    @staticmethod
    def get_location(search_input: str) -> dict:
        try:
            geolocator = Nominatim(user_agent="propiq_valuation_app")
            location = geolocator.geocode(search_input)
            if location:
                return {
                    "address": location.address,
                    "lat": location.latitude,
                    "lon": location.longitude,
                }
        except Exception as e:
            return {"error": str(e)}
        return {}


class AISummaryGenerator:
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    @staticmethod
    def _sanitize(text: str) -> str:
        replacements = {
            "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u00a0": " ",
            "\u2022": "-", "\u00b7": "-", "\u2012": "-", "\u2015": "-",
        }
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        return text.encode("latin-1", errors="replace").decode("latin-1")

    @staticmethod
    def generate(data: dict, api_key: str = "") -> str:
        if not api_key:
            api_key = get_effective_api_key()

        val_date = data.get("f) Valuation date")
        rep_date = data.get("m) Date of report")
        parts    = data.get("q) Selected Property Parts", [])

        context = (
            f"Valuer: {data.get('a) Identification and status of the valuer', 'N/A')}\n"
            f"Client: {data.get('b) Client details', 'N/A')}\n"
            f"Purpose of Valuation: {data.get('c) Purpose of the valuation', 'N/A')}\n"
            f"Property Identification: {data.get('d) Identification of the property', 'N/A')}\n"
            f"Basis of Value: {data.get('e) Basis of value adopted', 'N/A')}\n"
            f"Valuation Date: {val_date.strftime('%Y-%m-%d') if val_date else 'N/A'}\n"
            f"Nature of Property: {data.get('g) Nature of the property', 'N/A')}\n"
            f"Site Profile: {data.get('h) Site profile', 'N/A')}\n"
            f"Location: {data.get('Location Address', 'N/A')}\n"
            f"Market Value Evidence: {data.get('i) Market value evidence', 'N/A')}\n"
            f"Assumptions & Reservations: {data.get('j) Assumptions and reservations', 'N/A')}\n"
            f"Valuation Approach: {data.get('k) Valuation approach', 'N/A')}\n"
            f"Valuation Amount: LKR {data.get('l) Amount of valuation', 'N/A')}\n"
            f"Date of Report: {rep_date.strftime('%Y-%m-%d') if rep_date else 'N/A'}\n"
            f"Property Parts Inspected: {', '.join(parts) if parts else 'N/A'}\n"
        )

        prompt = (
            "You are a professional Chartered Valuation Surveyor writing an official valuation report.\n\n"
            "Using ALL of the valuation data provided below, write a comprehensive PROPERTY SUMMARY "
            "(250 to 300 words) to appear at the end of the valuation report. "
            "The summary MUST reference and incorporate every piece of information the valuer entered. "
            "Structure it in flowing prose paragraphs with NO bullet points, covering:\n"
            "1. Identity of the property and the client\n"
            "2. Purpose and basis of the valuation\n"
            "3. Nature and use/occupancy of the property\n"
            "4. Site characteristics, location and building profile\n"
            "5. Market value evidence and comparable data\n"
            "6. Assumptions and reservations applied\n"
            "7. Valuation approach and methodology\n"
            "8. Final assessed market value and date\n\n"
            "Use ONLY plain ASCII characters. Do NOT use em dashes, smart quotes, or special symbols.\n"
            "Write in formal third-person professional language.\n\n"
            f"VALUATION DATA:\n{context}"
        )

        if not api_key or len(api_key) < 10:
            return "AI summary unavailable: No Google Gemini API key configured in .env or settings."

        model = SessionManager.get("google_api_model") or "gemini-2.5-flash"
        url     = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.2},
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
                        return f"AI summary temporarily unavailable: Too many requests (API rate limited). Details: {err_msg}"

                if resp.status_code in (401, 403):
                    return "AI summary unavailable: Invalid or unauthorised Google API key."
                if resp.status_code == 400:
                    try:
                        err_msg = resp.json()["error"]["message"]
                    except Exception:
                        err_msg = resp.text[:200]
                    return f"AI summary unavailable: Bad request. Details: {err_msg}"
                
                resp.raise_for_status()
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return AISummaryGenerator._sanitize(raw)
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                return "AI summary unavailable: Request timed out."
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                return (
                    "This valuation report presents a professional assessment of the subject property "
                    "as described in the sections above. The valuation has been conducted in accordance "
                    "with recognised valuation standards and reflects prevailing market conditions. "
                    f"[Error: {str(e)}]"
                )