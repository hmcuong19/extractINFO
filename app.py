import streamlit as st
import google.generativeai as genai
import io
import docx
import fitz  # PyMuPDF

# --- Cấu hình và Thiết lập ---

# Thiết lập tiêu đề và icon cho trang, sử dụng layout rộng để có 2 cột
st.set_page_config(page_title="Trích xuất Thông tin Thông minh", page_icon="✨", layout="wide")

# Lấy API key từ secrets của Streamlit để bảo mật
# Hướng dẫn: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
try:
    # Cố gắng lấy key từ Streamlit's secrets management
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except (KeyError, FileNotFoundError):
    # Nếu không tìm thấy trong secrets (khi chạy local), yêu cầu người dùng nhập thủ công
    st.warning("Không tìm thấy Google API Key trong Streamlit secrets. Vui lòng nhập thủ công để chạy ứng dụng.")
    GOOGLE_API_KEY = st.text_input("Nhập Google API Key của bạn:", type="password")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        # Dừng ứng dụng nếu không có key để tránh lỗi
        st.info("Vui lòng cung cấp API key để bắt đầu.")
        st.stop()

# --- Các hàm xử lý ---

def get_gemini_response(input_text, prompt):
    """
    Hàm gọi Gemini API để lấy phản hồi dựa trên văn bản và prompt.
    Sử dụng model 'gemini-1.0-pro' là phiên bản ổn định.
    """
    # CẬP NHẬT: Thay đổi tên model thành 'gemini-1.0-pro' để sửa lỗi 404
    model = genai.GenerativeModel('gemini-1.0-pro')
    try:
        response = model.generate_content([input_text, prompt])
        return response.text
    except Exception as e:
        # Bắt lỗi và trả về thông báo thân thiện
        return f"Đã xảy ra lỗi khi gọi API Gemini: {e}"

def extract_text_from_docx(file_bytes):
    """
    Hàm trích xuất toàn bộ văn bản từ file .docx.
    Sử dụng io.BytesIO để đọc file từ bộ nhớ.
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        st.error(f"Lỗi đọc file .docx: {e}")
        return None

def extract_text_from_pdf(file_bytes):
    """
    Hàm trích xuất toàn bộ văn bản từ file .pdf bằng PyMuPDF.
    """
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

# --- Giao diện ứng dụng Streamlit ---

st.title("✨ Trích xuất Thông tin từ Tài liệu với Gemini Pro")
st.markdown("Tải lên tệp `.docx` hoặc `.pdf` và sử dụng prompt để yêu cầu Gemini trích xuất các trường thông tin bạn cần.")

# Tạo hai cột với tỉ lệ chiều rộng 2:3
col1, col2 = st.columns([2, 3])

with col1:
    st.header("1. Tải lên & Tùy chỉnh")

    # Widget tải file
    uploaded_file = st.file_uploader("Chọn một tệp (.docx hoặc .pdf)", type=['docx', 'pdf'])

    # CẬP NHẬT: Thay đổi prompt mặc định để trích xuất thông tin đề cương học phần
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

Nếu không tìm thấy thông tin nào, hãy ghi là "Không tìm thấy".
"""
    prompt_user = st.text_area("Chỉnh sửa prompt (câu lệnh yêu cầu):", value=prompt_default, height=350)

    # Nút xử lý
    submit_button = st.button("🚀 Bắt đầu trích xuất")

with col2:
    st.header("2. Kết quả trích xuất")

    # Vùng chứa kết quả, sử dụng st.container() để có thể cập nhật nội dung
    result_container = st.container()
    result_container.info("Kết quả sẽ được hiển thị ở đây sau khi bạn nhấn nút 'Bắt đầu trích xuất'.")

    # Xử lý logic khi người dùng nhấn nút
    if submit_button:
        if uploaded_file is not None and prompt_user:
            # Hiển thị spinner trong khi xử lý
            with st.spinner("Đang đọc file và gửi yêu cầu đến Gemini... Vui lòng chờ! 🤖"):
                # Đọc file dưới dạng bytes
                file_bytes = uploaded_file.getvalue()
                
                # Xác định loại file và trích xuất văn bản
                file_extension = uploaded_file.name.split('.')[-1].lower()
                raw_text = None
                if file_extension == "docx":
                    raw_text = extract_text_from_docx(file_bytes)
                elif file_extension == "pdf":
                    raw_text = extract_text_from_pdf(file_bytes)

                # Gọi Gemini API và hiển thị kết quả
                if raw_text:
                    response = get_gemini_response(raw_text, prompt_user)
                    result_container.text_area("Thông tin đã trích xuất:", value=response, height=550)
                else:
                    result_container.error("Không thể đọc được nội dung từ file đã tải lên. File có thể bị lỗi hoặc trống.")
        # Các trường hợp lỗi đầu vào từ người dùng
        elif not uploaded_file:
            st.warning("Vui lòng tải lên một file để tiếp tục.")
        else:
            st.warning("Prompt không được để trống.")
