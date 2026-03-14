import fitz
import re


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF bytes. Returns (full_text, page_count)."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append(text.strip())
    page_count = len(doc)
    doc.close()
    full_text = "\n\n".join(pages)
    return full_text, page_count


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace and artifacts."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    text = text.strip()
    return text


def detect_metadata(filename: str) -> dict:
    """Extract grade and subject from filename like peblo_pdf_grade4_english_grammar.pdf."""
    metadata = {"grade": None, "subject": None}
    filename_lower = filename.lower()

    grade_match = re.search(r'grade(\d+)', filename_lower)
    if grade_match:
        metadata["grade"] = int(grade_match.group(1))

    subject_map = {
        "math": "Math",
        "english": "English",
        "science": "Science",
        "grammar": "English",
    }
    for key, value in subject_map.items():
        if key in filename_lower:
            metadata["subject"] = value
            break

    return metadata
