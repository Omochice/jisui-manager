import glob
import os
import re
import sys
import tempfile
from pathlib import Path

import pdf2image
import pyocr
import PyPDF2


def scan_isbn(input_file: str, n_use_pages: int = 7) -> str:
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
        スキャン結果得られたISBNコード(978から始まる13桁)
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


if __name__ == "__main__":

    project_dir = Path(__file__).resolve().parents[1]
    print(project_dir)
    for book in glob.glob(os.path.join(project_dir, "test_books/*.pdf")):
        print(book)
        print(scan_isbn(book))
