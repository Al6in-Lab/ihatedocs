import tempfile
from pathlib import Path
import streamlit as st
from document_converter import CONVERTERS

st.set_page_config(page_title="ihatedocs", layout="centered")

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

with st.container(border=True):
    picked = st.selectbox("Pick conversion", list(LABELS.values()))
    conv_key = next(k for k, v in LABELS.items() if v == picked)
    ext = conv_key.split("_to_")[0]

    uploaded = st.file_uploader(f"Drop your .{ext} file here", type=[ext])

    if uploaded and st.button("Convert", type="primary"):
        with st.spinner("converting..."):
            try:
                # use a temp dir so files get wiped right after download
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    in_file = tmp_path / uploaded.name
                    in_file.write_bytes(uploaded.getvalue())

                    out_file = CONVERTERS[conv_key](in_file, output_dir=tmp_path)
                    file_bytes = out_file.read_bytes()

                st.success(f"Ready: {out_file.name}")
                st.download_button(
                    label=f"Download {out_file.name}",
                    data=file_bytes,
                    file_name=out_file.name,
                )
            except Exception as err:
                st.error(f"failed: {err}")

st.caption("files are processed in temp memory and deleted right away. source on [github](https://github.com/Al6in-Lab/ihatedocs)")
