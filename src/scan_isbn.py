import re
import sys
import tempfile

import pyocr
import PyPDF2

import pdf2image


def scan_isbn(input_file: str, n_use_pages: int = 7) -> str:
    """入力されたパスのPDFを読み取りISBN番号を返す
    """

    with open(input_file, "rb") as f:
        n_pages = PyPDF2.PdfFileReader(f).getNumPages()

    with tempfile.TemporaryDirectory() as tmp_dir:
        end_of_pages = pdf2image.convert_from_path(input_file,
                                                   first_page=n_pages - n_use_pages,
                                                   output_folder=tmp_dir,
                                                   fmt="jpeg")

        for page in end_of_pages:
            ocr_rst = pyocr.tesseract.image_to_string(
                page, builder=pyocr.builders.TextBuilder(tesseract_layout=3))
            execlude_space = ocr_rst.replace(" ", "").replace("-", "")
            if re.search(r'ISBN978[0-9]{10}', execlude_space):
                return re.findall(r'978[0-9]{10}', execlude_space).pop()


def fetch_book_info(isbn_code: int) -> dict:
    pass


if __name__ == "__main__":
    scan_isbn("/home/mochi/Pictures/Pythonからはじめる数学入門.pdf")