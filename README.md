# Document Converter

A lightweight Python document converter supporting **TXT**, **PDF**, and **DOCX** conversions in both directions (`TXT ↔ PDF`, `DOCX ↔ PDF`, and `DOCX ↔ TXT`).

🔗 **Live Web App:** [Click here to use the online converter](https://streamlit.app) *(Replace with your Streamlit URL once deployed)*

---

## Features
* **TXT → PDF** (`fpdf2`)
* **PDF → TXT** (`pypdf`)
* **DOCX → PDF** (`LibreOffice`)
* **PDF → DOCX** (`LibreOffice`)
* **DOCX → TXT** (`python-docx`)
* **TXT → DOCX** (`python-docx`)

---

## Local Setup (`git clone`)

### 1. Clone the repository
```bash
git clone https://github.com/Al6in-Lab/ihatedocs
cd ihatedocs
```

### 2. Install LibreOffice (Required for DOCX ↔ PDF conversions)
On Debian, Ubuntu, or MiniOS Linux, install the lightweight Writer engine:
```bash
sudo apt update && sudo apt install -y --no-install-recommends libreoffice-writer
```
*(Note: If you only need `TXT ↔ PDF` or `DOCX ↔ TXT`, you can skip LibreOffice.)*

### 3. Install Python dependencies
Create a virtual environment and install the required packages:
```bash
python3 -m venv venv
source venv/bin/activate
pip install fpdf2 pypdf python-docx
```
*(Optional: Run `pip install -r requirements.txt` if you also want to run the Streamlit web UI locally.)*

---

## Usage

### Run the Terminal CLI (`document_converter.py`)
```bash
python3 document_converter.py
```

### Run the Web Interface Locally (`app.py`)
```bash
streamlit run app.py
```

### Use as a Python Module
You can also import the converter functions directly into your own Python scripts:
```python
from document_converter import docx_to_pdf, pdf_to_txt

docx_to_pdf("example.docx", output_dir="./output")
pdf_to_txt("example.pdf", output_dir="./output")
```
