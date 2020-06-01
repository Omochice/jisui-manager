import glob
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pdf2image
import pyocr
import PyPDF2


def scan_isbn(input_file: str, n_use_pages: int = 7) -> Optional[str]:
    """入力されたパスのPDFを読み取りISBN番号を返す

    Parameters
    ----------
    input_file: str
        スキャン対象のpdfファイルへのPath
    n_use_pages: int
        最後から何ページをスキャン対象とするか
    
    Returns
    -------
    ISBN_code: str
        スキャンの結果得られたISBNコード(978から始まる13桁、または旧コードの10桁)
    """

    with open(input_file, "rb") as f:
        n_pages = PyPDF2.PdfFileReader(f).getNumPages()

    with tempfile.TemporaryDirectory() as tmp_dir:
        end_of_pages = pdf2image.convert_from_path(input_file,
                                                   first_page=n_pages - n_use_pages,
                                                   output_folder=tmp_dir,
                                                   fmt="jpeg")

        isbn_code = None

        for page in end_of_pages[::-1]:
            ocr_rst = pyocr.tesseract.image_to_string(page, lang="eng")
            execlude_space = ocr_rst.replace(" ", "").replace("-", "")
            if isbn_code := re.search(r'ISBN([0-9]{13})', execlude_space):
                return isbn_code.group(1)
            elif isbn_code := re.search(r'ISBN([0-9]{10})', execlude_space):
                return isbn_code.group(1)


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parents[1]
    print(project_dir)
    for book in glob.glob(os.path.join(project_dir, "test_books/*.pdf")):
        print(book)
        print(scan_isbn(book))
