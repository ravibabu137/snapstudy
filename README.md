# 📚 SnapStudy

An AI study buddy built with Streamlit and Gemini. Snap a photo of a problem,
diagram, or page of notes (or type a question) and get a plain-language
explanation. One button emails you a summary of the session.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:
   - a Gemini API key from aistudio.google.com
   - a Gmail address and App Password (myaccount.google.com/apppasswords)
3. Run: `streamlit run app.py`

🔗 **Live app:** https://snapstudy-xtir3uatwj2gcka9p42tkw.streamlit.app/