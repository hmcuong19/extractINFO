import streamlit as st
import google.generativeai as genai
import io
import docx
import fitz  # PyMuPDF

# --- Cấu hình và Thiết lập ---

# Thiết lập tiêu đề và icon cho trang
st.set_page_config(page_title="Trích xuất Thông tin Thông minh", page_icon="✨", layout="wide")

# Lấy API key từ secrets của Streamlit
try:
    # Cố gắng lấy key từ Streamlit's secrets management
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except (KeyError, FileNotFoundError):
    # Nếu không tìm thấy, yêu cầu người dùng nhập thủ công
    st.warning("Không tìm thấy Google API Key trong Streamlit secrets. Vui lòng nhập thủ công.")
    GOOGLE_API_KEY = st.text_input("Nhập Google API Key của bạn:", type="password")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        st.stop() # Dừng ứng dụng nếu không có key

# --- Hàm xử lý ---

def get_gemini_response(input_text, prompt):
    """
    Hàm gọi Gemini API để lấy phản hồi dựa trên văn bản và prompt.
    """
    model = genai.GenerativeModel('gemini-pro')
    try:
        response = model.generate_content([input_text, prompt])
        return response.text
    except Exception as e:
        return f"Đã xảy ra lỗi: {e}"

def extract_text_from_docx(file):
    """
    Hàm trích xuất toàn bộ văn bản từ file .docx.
    """
    doc = docx.Document(io.BytesIO(file.read()))
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract_text_from_pdf(file):
    """
    Hàm trích xuất toàn bộ văn bản từ file .pdf.
    """
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    full_text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        full_text += page.get_text()
    return full_text

# --- Giao diện ứng dụng ---

st.title("✨ Trích xuất Thông tin từ Tài liệu với Gemini Pro")
st.write("Tải lên tệp .docx hoặc .pdf và sử dụng prompt để yêu cầu Gemini trích xuất các trường thông tin bạn cần.")

# Tạo hai cột
col1, col2 = st.columns([2, 3])  # Tỉ lệ chiều rộng cột

with col1:
    st.header("1. Tải lên & Tùy chỉnh")

    # Widget tải file
    uploaded_file = st.file_uploader("Chọn một tệp (.docx hoặc .pdf)", type=['docx', 'pdf'])

    # Prompt mặc định và cho phép chỉnh sửa
    prompt_default = """
    Bạn là một trợ lý AI chuyên nghiệp trong việc trích xuất thông tin.
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
    prompt_user = st.text_area("Chỉnh sửa prompt của bạn:", value=prompt_default, height=300)

    # Nút xử lý
    submit_button = st.button("🚀 Bắt đầu trích xuất")

with col2:
    st.header("2. Kết quả trích xuất")

    # Vùng chứa kết quả
    result_box = st.empty()
    result_box.info("Kết quả sẽ được hiển thị ở đây sau khi bạn nhấn nút 'Bắt đầu trích xuất'.")

    # Xử lý khi người dùng nhấn nút
    if submit_button:
        if uploaded_file is not None and prompt_user:
            with st.spinner("Đang đọc file và gửi yêu cầu đến Gemini... Vui lòng chờ! 🤖"):
                # Đọc nội dung file
                file_extension = uploaded_file.name.split('.')[-1].lower()
                if file_extension == "docx":
                    raw_text = extract_text_from_docx(uploaded_file)
                elif file_extension == "pdf":
                    raw_text = extract_text_from_pdf(uploaded_file)
                else:
                    st.error("Định dạng file không được hỗ trợ!")
                    st.stop()

                # Gọi Gemini API và hiển thị kết quả
                if raw_text:
                    response = get_gemini_response(raw_text, prompt_user)
                    result_box.text_area("Thông tin đã trích xuất:", value=response, height=500, disabled=True)
                else:
                    result_box.warning("Không thể đọc được nội dung từ file đã tải lên.")
        elif not uploaded_file:
            st.warning("Vui lòng tải lên một file để tiếp tục.")
        else:
            st.warning("Prompt không được để trống.")
