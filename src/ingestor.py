import os
import re
from typing import List
import fitz  # PyMuPDF
from src.models import DocumentChunk


def clean_vietnamese_text(text: str) -> str:
    """Clean text, normalize extra whitespace while preserving Vietnamese accents."""
    if not text:
        return ""
    # Replace linebreaks with spaces
    text = re.sub(r'[\r\n]+', ' ', text)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_pdf_chunks(pdf_path: str, company_name: str = "Vinamilk", chunk_size: int = 1000, overlap: int = 150) -> List[DocumentChunk]:
    """
    Extract text from PDF page by page, clean text, and chunk into DocumentChunk objects.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    chunks: List[DocumentChunk] = []
    chunk_counter = 0

    print(f"📖 Opening PDF: {filename} ({len(doc)} pages)...")

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        raw_text = page.get_text("text")
        cleaned_text = clean_vietnamese_text(raw_text)

        if not cleaned_text or len(cleaned_text) < 30:
            continue

        # Split text into overlapping chunks
        start = 0
        text_len = len(cleaned_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Adjust end to avoid cutting words in half
            if end < text_len:
                last_space = cleaned_text.rfind(' ', start, end)
                if last_space > start + (chunk_size // 2):
                    end = last_space

            chunk_text = cleaned_text[start:end].strip()

            if len(chunk_text) >= 50:
                chunk_counter += 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"chunk_{chunk_counter}",
                        company_name=company_name,
                        source_file=filename,
                        page_number=page_num,
                        text_content=chunk_text
                    )
                )

            start = end - overlap if (end - overlap) > start else end

    print(f"✅ Extracted {len(chunks)} text chunks from PDF.")
    return chunks


if __name__ == "__main__":
    sample_pdf = r"d:\ESG\data\VNMSR_Full_VN_Smart_PDF_0807_compressed_614c2277d9.pdf"
    if os.path.exists(sample_pdf):
        res = extract_pdf_chunks(sample_pdf)
        print(f"Sample Chunk 1 (Page {res[0].page_number}): {res[0].text_content[:200]}...")
