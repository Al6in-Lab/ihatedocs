import tempfile
from pathlib import Path
import streamlit as st
from document_converter import CONVERTERS
 
st.set_page_config(page_title="ihatedocs", layout="centered")
 
MAX_MB = 50  # keeps the free cloud tier from running out of memory
 
MIMES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
 
# keep the page narrow and buttons full width so it looks decent
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 650px;
    }
    div.stButton > button, div.stDownloadButton > button {
        width: 100%;
        border-radius: 6px;
        padding: 0.55rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
 
st.title("ihatedocs")
st.caption("simple txt, pdf, and docx converter")
 
# map nice dropdown labels to the actual function names
LABELS = {
    "txt_to_pdf": "TXT -> PDF",
    "pdf_to_txt": "PDF -> TXT",
    "docx_to_pdf": "DOCX -> PDF",
    "pdf_to_docx": "PDF -> DOCX",
    "docx_to_txt": "DOCX -> TXT",
    "txt_to_docx": "TXT -> DOCX",
}
 
# the last finished conversion lives here so it survives the rerun
# that streamlit does when you click the download button
if "result" not in st.session_state:
    st.session_state.result = None
 
with st.container(border=True):
    picked = st.selectbox("Pick conversion", list(LABELS.values()))
    conv_key = next(k for k, v in LABELS.items() if v == picked)
    ext = conv_key.split("_to_")[0]
 
    if conv_key == "pdf_to_docx":
        st.caption("works best on PDFs with real text. scanned PDFs (photos of pages) need OCR first.")
 
    uploaded = st.file_uploader(f"Drop your .{ext} file here", type=[ext])
 
    # identifies "this file + this conversion" so an old result never shows for a new upload
    signature = (conv_key, uploaded.name, uploaded.size) if uploaded else None
 
    if uploaded and st.button("Convert", type="primary"):
        st.session_state.result = None
 
        if uploaded.size > MAX_MB * 1024 * 1024:
            st.error(f"file is too big, max is {MAX_MB} MB")
        else:
            with st.spinner("converting... (big PDFs can take a minute)"):
                try:
                    # use a temp dir so files get wiped right after conversion
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir)
                        # .name strips any folder parts from the uploaded filename
                        in_file = tmp_path / Path(uploaded.name).name
                        in_file.write_bytes(uploaded.getvalue())
 
                        out_file = CONVERTERS[conv_key](in_file, output_dir=tmp_path)
                        file_bytes = out_file.read_bytes()
 
                    st.session_state.result = {
                        "signature": signature,
                        "name": out_file.name,
                        "data": file_bytes,
                        "mime": MIMES.get(out_file.suffix.lower(), "application/octet-stream"),
                    }
                except Exception as err:
                    st.error(f"failed: {err}")
 
    result = st.session_state.result
    if uploaded and result and result["signature"] == signature:
        st.success(f"Ready: {result['name']}")
        st.download_button(
            label=f"Download {result['name']}",
            data=result["data"],
            file_name=result["name"],
            mime=result["mime"],
        )
 
st.caption("files are processed in temp memory and deleted right away. source on [github](https://github.com/Al6in-Lab/ihatedocs)")
 

