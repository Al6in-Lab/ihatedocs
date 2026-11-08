import shutil
import subprocess
import sys
from pathlib import Path
from docx import Document
from fpdf import FPDF
from pypdf import PdfReader


# quick helper to check if file exists and matches what we expect
def check_file(input_path, expected_ext):
    if not input_path.is_file():
        raise FileNotFoundError(f"cant find file: {input_path}")
    if input_path.suffix.lower() != expected_ext:
        raise ValueError(f"wrong file type, need {expected_ext} but got {input_path.suffix}")


# runs libreoffice in the background without opening the window
def run_libreoffice(args, timeout=60):
    if shutil.which("libreoffice") is None:
        raise RuntimeError("libreoffice isnt installed or not in PATH")
    try:
        subprocess.run(
            ["libreoffice", "--headless", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"libreoffice took too long (over {timeout}s)")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"libreoffice crashed: {e.stderr.strip()}")


def txt_to_pdf(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".txt")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # utf-8 so weird characters dont break on linux
    text = src.read_text(encoding="utf-8")
    pdf.multi_cell(w=0, h=8, text=text)
    pdf.output(str(out_file))
    return out_file


def pdf_to_txt(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".pdf")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.txt"

    reader = PdfReader(str(src))
    # grab text page by page, fallback to empty string if page is blank
    extracted = "\n".join((page.extract_text() or "") for page in reader.pages)
    out_file.write_text(extracted, encoding="utf-8")
    return out_file


def docx_to_pdf(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".docx")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.pdf"

    run_libreoffice(["--convert-to", "pdf", "--outdir", str(out_dir), str(src)])
    if not out_file.is_file():
        raise RuntimeError("libreoffice finished but didnt make the pdf")
    return out_file


def pdf_to_docx(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".pdf")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.docx"

    # try pdf2docx first on cloud server, fall back to libreoffice on older cpus (like minios)
    try:
        from pdf2docx import Converter

        cv = Converter(str(src))
        cv.convert(str(out_file))
        cv.close()
    except ImportError:
        run_libreoffice([
            "--infilter=writer_pdf_import",
            "--convert-to",
            "docx",
            "--outdir",
            str(out_dir),
            str(src),
        ])
    except Exception as e:
        raise RuntimeError(f"pdf to docx failed: {e}")

    if not out_file.is_file():
        raise RuntimeError("couldnt convert pdf, might be password locked or scanned")
    return out_file


def docx_to_txt(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".docx")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.txt"

    doc = Document(str(src))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    out_file.write_text(full_text, encoding="utf-8")
    return out_file


def txt_to_docx(input_path, output_dir="."):
    src = Path(input_path)
    check_file(src, ".txt")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{src.stem}.docx"

    doc = Document()
    for line in src.read_text(encoding="utf-8").splitlines():
        doc.add_paragraph(line)
    doc.save(str(out_file))
    return out_file


CONVERTERS = {
    "txt_to_pdf": txt_to_pdf,
    "pdf_to_txt": pdf_to_txt,
    "docx_to_pdf": docx_to_pdf,
    "pdf_to_docx": pdf_to_docx,
    "docx_to_txt": docx_to_txt,
    "txt_to_docx": txt_to_docx,
}


# basic terminal menu if someone clones and runs this locally
def run_cli():
    keys = list(CONVERTERS.keys())
    while True:
        print("\nConverters:", ", ".join(f"{i + 1}:{k}" for i, k in enumerate(keys)), "| 0:exit")
        choice = input("Select: ").strip()
        if choice == "0":
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
            print("invalid choice")
            continue

        func = CONVERTERS[keys[int(choice) - 1]]
        file_path = input("Path: ").strip("'\"")
        try:
            saved = func(file_path)
            print(f"done -> {saved}")
        except Exception as err:
            print(f"error: {err}", file=sys.stderr)


if __name__ == "__main__":
    try:
        run_cli()
    except (KeyboardInterrupt, EOFError):
        print("\nexiting...")
        sys.exit(0)
