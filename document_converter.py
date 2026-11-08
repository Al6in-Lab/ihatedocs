import shutil
import subprocess
import sys
from pathlib import Path
from docx import Document
from fpdf import FPDF
from pypdf import PdfReader


class ConversionError(Exception):
    """Custom exception raised when a document conversion fails."""


def _validate_input(input_path: Path, expected_ext: str) -> None:
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != expected_ext:
        raise ValueError(f"Expected a '{expected_ext}' file, got '{input_path.suffix}'")


def _run_libreoffice(args: list[str], timeout: int = 60) -> None:
    if shutil.which("libreoffice") is None:
        raise ConversionError("LibreOffice is not installed or not in system PATH.")
    try:
        subprocess.run(
            ["libreoffice", "--headless", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as err:
        raise ConversionError(f"LibreOffice timed out after {timeout}s.") from err
    except subprocess.CalledProcessError as err:
        raise ConversionError(f"LibreOffice error: {err.stderr.strip()}") from err


def txt_to_pdf(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".txt")
    out_file = Path(output_dir) / f"{src.stem}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    text = src.read_text(encoding="utf-8")
    pdf.multi_cell(w=0, h=8, text=text)
    pdf.output(str(out_file))
    return out_file


def pdf_to_txt(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".pdf")
    out_file = Path(output_dir) / f"{src.stem}.txt"

    reader = PdfReader(str(src))
    extracted = "\n".join((page.extract_text() or "") for page in reader.pages)
    out_file.write_text(extracted, encoding="utf-8")
    return out_file


def docx_to_pdf(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".docx")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _run_libreoffice(["--convert-to", "pdf", "--outdir", str(out_dir), str(src)])
    return out_dir / f"{src.stem}.pdf"


def pdf_to_docx(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".pdf")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _run_libreoffice([
        "--infilter=writer_pdf_import",
        "--convert-to",
        "docx",
        "--outdir",
        str(out_dir),
        str(src),
    ])
    return out_dir / f"{src.stem}.docx"


def docx_to_txt(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".docx")
    out_file = Path(output_dir) / f"{src.stem}.txt"

    doc = Document(str(src))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    out_file.write_text(full_text, encoding="utf-8")
    return out_file


def txt_to_docx(input_path: str | Path, output_dir: str | Path = ".") -> Path:
    src = Path(input_path)
    _validate_input(src, ".txt")
    out_file = Path(output_dir) / f"{src.stem}.docx"

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


def run_cli() -> None:
    keys = list(CONVERTERS.keys())
    while True:
        print("\nConverters:", ", ".join(f"{i + 1}:{k}" for i, k in enumerate(keys)), "| 0:exit")
        choice = input("Select: ").strip()
        if choice == "0":
            break
        if not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
            print("Invalid selection.")
            continue

        func = CONVERTERS[keys[int(choice) - 1]]
        file_path = input("Path: ").strip("'\"")
        try:
            saved = func(file_path)
            print(f"OK -> {saved}")
        except (FileNotFoundError, ValueError, ConversionError, OSError) as err:
            print(f"Error: {err}", file=sys.stderr)


if __name__ == "__main__":
    try:
        run_cli()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrupted. Exiting cleanly.")
        sys.exit(0)

