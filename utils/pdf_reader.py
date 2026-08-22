"""
utils/pdf_reader.py
--------------------
Simple PDF text extraction utility.

Usage (once PyMuPDF is added to requirements):
    from utils.pdf_reader import extract_text_from_pdf
    text = extract_text_from_pdf(uploaded_file)
"""

import io


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract plain text from an uploaded PDF file.

    Args:
        uploaded_file: A Streamlit UploadedFile object (or any file-like object).

    Returns:
        Extracted text as a single string, or an empty string if extraction fails.

    Note:
        This function requires PyMuPDF (fitz).
        Add 'PyMuPDF' to requirements.txt before calling this function.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return (
            "PDF extraction is not available. "
            "Install PyMuPDF: pip install PyMuPDF"
        )

    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()
        return "\n".join(pages_text).strip()
    except Exception as exc:
        return f"Could not read PDF: {exc}"


def get_page_count(uploaded_file) -> int:
    """
    Return the number of pages in an uploaded PDF file.

    Args:
        uploaded_file: A Streamlit UploadedFile object (or any file-like object).

    Returns:
        Page count as an integer, or 0 on failure.
    """
    try:
        import fitz
    except ImportError:
        return 0

    try:
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
