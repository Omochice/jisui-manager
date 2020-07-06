import re
import tempfile
from pathlib import Path
from typing import Optional, Union

import pdf2image
import pyocr
import PyPDF2


def scan_isbn(input_file: Union[str, Path], n_use_pages: int = 13) -> Optional[str]:
    """入力されたパスのPDFを読み取りISBN番号を返す 

    Args:
        input_file (str | Path): スキャン対象のpdfファイルへのPath
        n_use_pages (int, optional): 最後から何ページをスキャン対象とするか
        たまに背表紙+同版元の宣伝が3ページぐらい入っているのでカバー+背表紙+宣伝3ページぐらいを考慮し
        デフォルト値を13としている

    Returns:
        Optional[str]: スキャンの結果得られたISBNコード(978から始まる13桁、または旧コードの10桁)
        見つからなかったらNoneを返す（何も返さない）
    """

    with open(input_file, "rb") as f:
        n_pages = PyPDF2.PdfFileReader(f).getNumPages()

    with tempfile.TemporaryDirectory() as tmp_dir:
        end_of_pages = pdf2image.convert_from_path(input_file,
                                                   first_page=n_pages - n_use_pages,
                                                   output_folder=tmp_dir,
                                                   fmt="jpeg")

        isbn_code = None

        for page in end_of_pages[::-1]: # 後ろのほうがコードがある確率が高いので逆順
            ocr_rst = pyocr.tesseract.image_to_string(page, lang="eng") # 日本語と誤認識されたくない
            execlude_space = ocr_rst.replace(" ", "").replace("-", "")
            if isbn_code := re.search(r'ISBN([0-9]{13})', execlude_space):
                return isbn_code.group(1)
            elif isbn_code := re.search(r'ISBN([0-9]{10})', execlude_space):
                return isbn_code.group(1)


if __name__ == "__main__":
    print(scan_isbn("/media/mochi/HardDiskDri/scanbook_tmporary_dir/20200610050153.pdf"))
    # project_dir = Path(__file__).resolve().parents[1]
    # print(project_dir)
    # for book in glob.glob(os.path.join(project_dir, "test_books/*.pdf")):
    #     print(book)
    #     print(scan_isbn(book))
