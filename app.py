import streamlit as st
import google.generativeai as genai
import io
import docx
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="Trích xuất Thông tin Thông minh", page_icon="✨", layout="wide")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except (KeyError, FileNotFoundError):
    st.warning("Không tìm thấy Google API Key trong Streamlit secrets. Vui lòng nhập thủ công để chạy ứng dụng.")
    GOOGLE_API_KEY = st.text_input("Nhập Google API Key của bạn:", type="password")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        st.info("Vui lòng cung cấp API key để bắt đầu.")
        st.stop()

def get_gemini_response(input_text, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content([input_text, prompt])
        return response.text
    except Exception as e:
        return f"Đã xảy ra lỗi khi gọi API Gemini: {e}"

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        st.error(f"Lỗi đọc file .docx: {e}")
        return None

def extract_text_from_pdf(file_bytes):
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text()
        pdf_document.close()
        return full_text
    except Exception as e:
        st.error(f"Lỗi đọc file .pdf: {e}")
        return None

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
        st.error(f"❌ Lỗi chuyển DOCX sang PDF tạm: {e}")
        return None

st.title("✨ Trích xuất Thông tin từ Tài liệu với Gemini Pro")
st.markdown("Tải lên tệp `.docx` hoặc `.pdf` và sử dụng prompt để yêu cầu Gemini trích xuất các trường thông tin bạn cần.")

col1, col2 = st.columns([2, 3])

with col1:
    st.header("1. Tải lên & Tùy chỉnh")

    uploaded_file = st.file_uploader("Chọn một tệp (.docx hoặc .pdf)", type=['docx', 'pdf'])

    prompt_default = """Bạn là một trợ lý AI chuyên nghiệp trong việc trích xuất thông tin.
Dựa vào nội dung văn bản được cung cấp, hãy tách và liệt kê các thông tin sau:
Từ nội dung đề cương học phần dưới đây, hãy trích xuất và trình bày rõ ràng các mục sau:
Tên học phần
Mã học phần (nếu có)
Số tín chỉ
Điều kiện tiên quyết (nếu có)
Mục tiêu học phần
Chuẩn đầu ra của học phần (CLO)
Nội dung học phần tóm tắt
Tài liệu tham khảo (ghi rõ tên, tác giả, năm, NXB nếu có)

Trình bày câu trả lời theo định dạng rõ ràng như sau:
Tên học phần: ...
Mã học phần: ...
Số tín chỉ: ...
Điều kiện tiên quyết: ...
Mục tiêu học phần:
- ...
- ...
Chuẩn đầu ra:
- CLO1: ...
- CLO2: ...
...
Tóm tắt nội dung học phần:
- Tuần 1: ...
- Tuần 2: ...
...
Tài liệu tham khảo:
- ...
- ...

Nếu không tìm thấy thông tin nào, hãy ghi là \"Không tìm thấy\".
"""
    prompt_user = st.text_area("Chỉnh sửa prompt (câu lệnh yêu cầu):", value=prompt_default, height=350)
    submit_button = st.button("🚀 Bắt đầu trích xuất")

with col2:
    st.header("2. Kết quả trích xuất")
    result_container = st.container()
    result_container.info("Kết quả sẽ được hiển thị ở đây sau khi bạn nhấn nút 'Bắt đầu trích xuất'.")

    if submit_button:
        if uploaded_file is not None and prompt_user:
            with st.spinner("Đang đọc file và gửi yêu cầu đến Gemini... Vui lòng chờ! 🤖"):
                file_bytes = uploaded_file.getvalue()
                file_extension = uploaded_file.name.split('.')[-1].lower()
                raw_text = None

                if file_extension == "docx":
                    pdf_bytes = convert_docx_to_pdf_bytes(file_bytes)
                    if pdf_bytes:
                        raw_text = extract_text_from_pdf(pdf_bytes)
                elif file_extension == "pdf":
                    raw_text = extract_text_from_pdf(file_bytes)

                if raw_text:
                    response = get_gemini_response(raw_text, prompt_user)
                    result_container.markdown(response, unsafe_allow_html=False)
                else:
                    result_container.error("Không thể đọc được nội dung từ file đã tải lên. File có thể bị lỗi hoặc trống.")
        elif not uploaded_file:
            st.warning("Vui lòng tải lên một file để tiếp tục.")
        else:
            st.warning("Prompt không được để trống.")
