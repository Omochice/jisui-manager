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

        for page in end_of_pages[::-1]:    # 後ろのほうがコードがある確率が高いので逆順
            ocr_rst = pyocr.tesseract.image_to_string(page,
                                                      lang="eng")    # 日本語と誤認識されたくない
            execlude_space = ocr_rst.replace(" ", "").replace("-", "")

            # print(execlude_space)

            isbn_code = (re.search(r'[Ii][Ss][Bb][Nn]([0-9]{12,13})', execlude_space)
                         or re.search(r'[Ii][Ss][Bb][Nn]([0-9X]{9,10})', execlude_space)
                         or re.search(r"(978[0-9]{9,10})", execlude_space))
            if isbn_code:
                return modify_missing(isbn_code.group(1))


def modify_missing(isbn: str):
    n_code = len(isbn)
    total = 0
    if n_code == 12:    # isbn13の末尾欠損
        for i, number in zip(range(n_code), map(int, isbn)):
            total += number * (1 + 2 * (i % 2))
        c = (10 - (total % 10)) % 10
        isbn += str(c)
    elif n_code == 9:    # isbn10の末尾欠損
        for i, number in zip(range(n_code), map(int, isbn)):
            total += (10 - i) * number
        c = (11 - total % 11) % 11
        if c == 10:
            c = "X"
        isbn += str(c)
    return isbn


if __name__ == "__main__":
    pass
    # print(modify_missing("409126168"))
    # project_dir = Path(__file__).resolve().parents[1]
    # print(project_dir)
    # for book in glob.glob(os.path.join(project_dir, "test_books/*.pdf")):
    #     print(book)
    #     print(scan_isbn(book))
