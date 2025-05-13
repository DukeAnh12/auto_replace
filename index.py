import streamlit as st
import re

st.title("ZPL Template Replacer")

# File upload
template_file = st.file_uploader("Upload Template File", type=["txt", "zpl", "prn"])
data_file = st.file_uploader("Upload Data File (containing ^FNx^FD...^FS)", type=["txt", "zpl", "prn"])

def extract_data_from_zpl_data(data_content):
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

def replace_fn_in_template(template_content, data_dict):
    """Thay ^FNx bằng ^FD<value> trong template"""
    output_lines = []
    for line in template_content.splitlines():
        if line == "^DFBOARDPASS^FS":
            continue  # Bỏ qua dòng này
        match = re.search(r"\^FN(\d+)", line)
        if match:
            fn_key = f"FN{match.group(1)}"
            if fn_key in data_dict:
                value = data_dict[fn_key]
                replaced_line = re.sub(r"\^FN\d+", f"^FD{value}", line)
                output_lines.append(replaced_line)
            else:
                output_lines.append(line)  # giữ nguyên nếu không có dữ liệu
        else:
            output_lines.append(line)
    return "\n".join(output_lines)

# Khi cả hai file đều được tải lên
if template_file and data_file:
    try:
        # Đọc nội dung file
        template_content = template_file.read().decode("utf-8")
        data_content = data_file.read().decode("utf-8")

        # Parse data và thay thế
        data_dict = extract_data_from_zpl_data(data_content)
        result = replace_fn_in_template(template_content, data_dict)
        
        # Cho phép tải xuống
        st.download_button("Tải về ZPL đã thay", result, file_name="output.zpl", mime="text/plain")

        # Hiển thị kết quả
        st.subheader("Kết quả sau khi thay thế:")
        st.code(result, language="zpl")

    except Exception as e:
        st.error(f"Lỗi: {e}")
