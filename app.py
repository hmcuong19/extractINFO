import streamlit as st
import tempfile
import os
import requests
import json
import io

from PyPDF2 import PdfReader
import docx
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="AI File Prompt Processor (Gemini)")
st.title("📄 AI Document Processor with Gemini Pro")
st.markdown("Upload a **.pdf** or **.docx** file, enter a prompt, and process it using Google Gemini API.")

uploaded_file = st.file_uploader("Choose a file (PDF or DOCX)", type=["pdf", "docx"])
user_prompt = st.text_area("Enter your prompt")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    gemini_api_key = st.text_input("Enter your Gemini API key", type="password")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def convert_docx_to_pdf_bytes(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                c.drawString(50, y, text)
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception as e:
        st.error(f"❌ Failed to convert DOCX to PDF: {e}")
        return None

if st.button("Process"):
    if not uploaded_file or not user_prompt or not gemini_api_key:
        st.warning("Please provide a file, prompt, and API key.")
        st.stop()

    ext = uploaded_file.name.split('.')[-1].lower()
    text = ""

    if ext == "pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        reader = PdfReader(tmp_file_path)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif ext == "docx":
        file_bytes = uploaded_file.read()
        pdf_bytes = convert_docx_to_pdf_bytes(file_bytes)
        if pdf_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(pdf_bytes)
                tmp_pdf_path = tmp_pdf.name
            reader = PdfReader(tmp_pdf_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            st.stop()

    else:
        st.error("Unsupported file type.")
        st.stop()

    full_prompt = f"Document Content:\n{text}\n\nUser Request:\n{user_prompt}"

    with st.spinner("Processing with Gemini Pro..."):
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            response = requests.post(
                f"{GEMINI_API_URL}?key={gemini_api_key}",
                headers=headers,
                data=json.dumps(payload)
            )
            result = response.json()

            if "candidates" in result and result["candidates"]:
                output = result["candidates"][0]["content"]["parts"][0]["text"]
                st.success("✅ Response:")
                st.write(output)
            else:
                st.error("❌ Gemini API did not return a valid response. Check your prompt or API key.")
                st.subheader("Raw API response:")
                st.json(result)

        except Exception as e:
            st.error(f"❌ Error: {e}")
