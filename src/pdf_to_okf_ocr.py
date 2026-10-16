from pathlib import Path

import pytesseract
from pdf2image import convert_from_path

from pdf_to_okf import process_pdf

#Configuration

INPUT_DIR = Path(r"D:\EBook_OKF")
OUTPUT_DIR = Path("output")

POPPLER_PATH = r"C:\Users\nikit\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin"

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\nikit\Documents\projects\OKF\tesseract.exe"
)

# OCR Extraction

from pdf2image import convert_from_path, pdfinfo_from_path

def extract_text_ocr(pdf_path):

    print("Starting OCR...")

    # Get page count first
    info = pdfinfo_from_path(
        pdf_path,
        poppler_path=POPPLER_PATH
    )

    num_pages = info["Pages"]

    print(f"{pdf_path.name}: {num_pages} pages detected.")

    text = []

    for page_num in range(1, num_pages + 1):

        print(f"OCR page {page_num}/{num_pages}")

        # Render ONE page only
        image = convert_from_path(
            pdf_path,
            first_page=page_num,
            last_page=page_num,
            dpi=300,
            poppler_path=POPPLER_PATH
        )[0]

        page_text = pytesseract.image_to_string(
            image,
            lang="tam",
            config = "--oem 3 --psm 6"
        )

        text.append(page_text)

    print("OCR complete.")

    return "\n\n".join(text)

# MAIN

def main():

    OUTPUT_DIR.mkdir(exist_ok=True)

    for pdf_file in INPUT_DIR.rglob("*"):

        if not (
            pdf_file.is_file()
            and pdf_file.suffix.lower() == ".pdf"
        ):
            continue

        book_output_dir = OUTPUT_DIR / pdf_file.stem.strip()

        # Already processed?
        if (
            book_output_dir.exists()
            and any(book_output_dir.glob("chunk_*.md"))
        ):
            print(f"Skipping: {pdf_file.name}")
            continue

        print(f"OCR Processing: {pdf_file.name}")

        try:

            text = extract_text_ocr(pdf_file)

            process_pdf(
                pdf_file,
                OUTPUT_DIR,
                text
            )

        except Exception as e:

            print(f"Failed: {pdf_file}")
            print(e)


if __name__ == "__main__":
    main()