import streamlit as st
import re
import requests

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

        # Hiển thị kết quả ZPL
        st.subheader("Kết quả sau khi thay thế:")
        st.code(result, language="zpl", height=200)

        # Gọi hàm để lấy PDF từ API
        def get_zpl_image(zpl):
            url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/'
            files = {'file': zpl}
            headers = {'Accept': 'application/pdf'}  # Bạn có thể đổi thành 'image/png' để nhận file PNG
            response = requests.post(url, headers=headers, files=files, stream=True)

            if response.status_code == 200:
                return response.content  # Trả về nội dung PDF (hoặc PNG) của phản hồi
            else:
                st.error('Error: ' + response.text)
                return None

        # Gọi API để lấy PDF từ ZPL
        pdf_data = get_zpl_image(result)

        # Hiển thị PDF nếu có dữ liệu trả về
        if pdf_data:
            st.write("### Label PDF:")
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name="label.pdf",
                mime="application/pdf"
            )

    except Exception as e:
        st.error(f"Lỗi: {e}")
