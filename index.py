import streamlit as st
import re
import requests

st.title("🖨️ ZPL Template Replacer")

# --- Helper Functions ---
def read_uploaded_file(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8")
        return content
    except Exception:
        st.warning(f"Không đọc được nội dung của {uploaded_file.name}. Có thể không phải là file text.")
        return None

def extract_data_from_zpl(data_content):
    """Trích dữ liệu từ các dòng ^FNx^FD...^FS"""
    data_dict = {}
    pattern = r"\^FN(\d+)\^FD(.*?)\^FS"
    for line in data_content.splitlines():
        match = re.search(pattern, line.strip())
        if match:
            fn_key = f"FN{match.group(1)}"
            value = match.group(2).strip()
            data_dict[fn_key] = value
    return data_dict

def replace_fn_with_fd(template_content, data_dict):
    """Thay ^FNx bằng ^FD<value>"""
    output_lines = []
    template_type = ""
    for line in template_content.splitlines():
        if line == "^DFBOARDPASS^FS":
            template_type = "^DFBOARDPASS^FS"
            continue
        elif line == "^DFBAGTAG^FS":
            template_type = "^DFBAGTAG^FS"
            continue
        match = re.search(r"\^FN(\d+)", line)
        if match:
            fn_key = f"FN{match.group(1)}"
            value = data_dict.get(fn_key)
            if value:
                replaced_line = re.sub(r"\^FN\d+", f"^FD{value}", line)
                output_lines.append(replaced_line)
            else:
                output_lines.append(line)
        else:
            output_lines.append(line)
    return "\n".join(output_lines), template_type

def get_label_pdf(zpl_code, template_type):
    if template_type == "^DFBAGTAG^FS":
        url = 'http://api.labelary.com/v1/printers/8dpmm/labels/2x15/0/'
    elif template_type == "^DFBOARDPASS^FS":
        url = 'http://api.labelary.com/v1/printers/8dpmm/labels/3.5x7.5/0/'
    else:
        st.warning("Không xác định được template để gửi tới Labelary.")
        return None

    headers = {'Accept': 'application/pdf'}
    files = {'file': zpl_code}
    response = requests.post(url, headers=headers, files=files, stream=True)

    if response.status_code == 200:
        return response.content
    else:
        st.error("Labelary API Error: " + response.text)
        return None

# --- File Upload ---
template_file = st.file_uploader("📄 Upload Template File", type=["txt", "zpl", "prn", "pdf"])
data_file = st.file_uploader("📄 Upload Data File (chứa ^FNx^FD...^FS)", type=["txt", "zpl", "prn", "pdf"])

# --- Main Processing ---
if template_file and data_file:
    template_content = read_uploaded_file(template_file)
    data_content = read_uploaded_file(data_file)

    if template_content and data_content:
        # Tự động hoán đổi nếu file bị ngược
        if "^DFBOARDPASS^FS" in data_content or "^DFBAGTAG^FS" in data_content:
            template_content, data_content = data_content, template_content

        data_dict = extract_data_from_zpl(data_content)
        zpl_result, template_type = replace_fn_with_fd(template_content, data_dict)

        # Hiển thị và cho phép tải về
        st.subheader("🔧 Kết quả sau khi thay thế:")
        st.code(zpl_result, language="zpl", height=200)
        st.download_button("⬇️ Tải về ZPL đã thay", zpl_result, file_name="output.zpl", mime="text/plain")

        # Gửi sang Labelary để tạo PDF
        pdf_bytes = get_label_pdf(zpl_result, template_type)
        if pdf_bytes:
            st.write("📄 Xem hoặc tải nhãn PDF:")
            st.download_button("⬇️ Tải PDF", data=pdf_bytes, file_name="label.pdf", mime="application/pdf")
