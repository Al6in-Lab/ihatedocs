import tempfile
from pathlib import Path
import streamlit as st
from document_converter import CONVERTERS, ConversionError

st.title("Document Converter")

conversion_type = st.selectbox("Conversion", list(CONVERTERS.keys()))
expected_ext = "." + conversion_type.split("_to_")[0]
uploaded = st.file_uploader(f"Upload {expected_ext} file", type=[expected_ext.lstrip(".")])

if uploaded and st.button("Convert"):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_path = tmp_path / uploaded.name
            input_path.write_bytes(uploaded.getvalue())

            output_path = CONVERTERS[conversion_type](input_path, output_dir=tmp_path)
            st.download_button(
                label=f"Download {output_path.name}",
                data=output_path.read_bytes(),
                file_name=output_path.name,
            )
    except (FileNotFoundError, ValueError, ConversionError, OSError) as err:
        st.error(f"Conversion failed: {err}")
