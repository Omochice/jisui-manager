import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

import yaml

from databese import DatabaseCliant
from ehon import EhonDoesNotHaveDataError, EhonSearchCliant
from honto import HontoDoesNotHaveDataError, HontoSearchCliant
from mylogger import MyLogger
from scan_isbn import scan_isbn


def show_title() -> None:
    print("===============================================")
    print("    ####               #       ####   ####     ")
    print("    #   #              #       #   #  #   #    ")
    print("    #   #   ###   ###  #  #    #   ## #   #    ")
    print("    ####   #  ## #  ## # #     #    # ####     ")
    print("    #   #  #   # #   # ###     #    # #   #    ")
    print("    #   ## #   # #   # ###     #   ## #   ##   ")
    print("    #   #  #  ## #  ## #  #    #   #  #   #    ")
    print("    #####   ###   ###  #  ##   ####   #####    ")
    print("===============================================")


def send_err_dir(target: Path, dst: Path) -> None:
    """エラーが起きたpdfファイルを移動する

    Args:
        target (Path): 対象のpdf
        dst (Path): 行き先
    """
    dst = dst / "tmp"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target), dst)


def generate_config_file(config_path: Path) -> None:
    """configファイルがないときに生成を行う

    Args:
        config_path (Path): configファイルの置き場所
    """

    config = {
        "input_dir": "",
        "output_dir": "",
        "database_path": str(Path(__file__).resolve().parents[1] / "books.sqlite3")
    }

    print("Cannot find config file.")
    print("\tGenerating config file...")

    for key, value in config.items():
        if key == "input_dir":
            while True:
                path = Path(input(f"\tType {key} path: ")).resolve()
                if path.exists():
                    break
                else:
                    print("\tThe path is not exists...")
        elif key == "output_dir":
            path = Path(input(f"\tType {key} path: ")).resolve()
        elif key == "database_path":
            path = value
            print(f"\tChange database path (default {value}) ? [y/n]: ", end="")
            while True:
                input_line = input()
                if input_line in {"y", "Y", "yes"}:
                    path = Path(input(f"\tType {key}: ")).resolve()
                elif input_line in {"n", "N", "no"}:
                    break
                else:
                    print("Type [y/n]: ")
        else:
            path = ""
        config[key] = str(path)

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, allow_unicode=True)


def fetch_book_info_from_pdf(pdf_path: Path, honto: HontoSearchCliant,
                             ehon: EhonSearchCliant) -> dict:
    """単一pdfのパスからそのpdfの書籍情報を取得する

    Args:
        pdf_path (Path): pdfファイルのパス
        honto (HontoSearchCliant): Hontoの検索クライアント
        ehon (EhonSearchCliant): E-honの検索クライアント

    Raises:
        NotFoundIsbnError: pdfからISBNコードを検出できなかったエラー
        HontoDoesNotHaveDataError: Honto上にその書籍情報が登録されていないエラー

    Returns:
        dict: 書籍情報のdict
    """
    print(str(pdf_path))
    # isbnの取得
    isbn_code = scan_isbn(pdf_path)
    if isbn_code is None:
        raise NotFoundIsbnError(f"Not found isbn in {pdf_path=}")

    # 書籍情報の取得
    return fetch_book_info_from_isbn(isbn_code, honto, ehon)


def fetch_book_info_from_isbn(isbn: str, honto: HontoSearchCliant,
                              ehon: EhonSearchCliant) -> dict:
    """isbnを元に書籍情報を取得する

    Args:
        isbn (str): isbn.
        honto (HontoSearchCliant): Hontoの検索クライアント
        ehon (EhonSearchCliant): E-honの検索クライアント

    Raises:
        HontoDoesNotHaveDataError: Honto上にその書籍情報が登録されていないエラー

    Returns:
        dict: 書籍情報
    """
    try:
        book_info = honto.fetch_book_info(isbn)
    except HontoDoesNotHaveDataError as e:
        raise HontoDoesNotHaveDataError(e)

    # シリーズ名の取得
    try:
        series = ehon.fetch_series_name(isbn)
    except EhonDoesNotHaveDataError as e:
        series = None
    book_info["series"] = series
    book_info["isbn"] = isbn
    return book_info


def construct_dst(parent_path: Path, book_info: dict) -> Path:
    """ファイルの行き先を生成する

    Args:
        parent_path (Path): 大元のrootとなるpath
        book_info (dict): 書籍情報

    Returns:
        Path: 生成されたpath
    """
    if book_info["category"] in {"漫画・コミック", "ライトノベル"}:
        series = book_info["series"] or book_info["sub_category"] or "未分類"
        dst = Path(parent_path, book_info["category"], series,
                   book_info["title"] + ".pdf")
    else:
        dst = Path(parent_path, book_info["category"], book_info["sub_category"],
                   book_info["series"] or "", book_info["title"] + ".pdf")
    return dst


class NotFoundIsbnError(Exception):
    pass


def main():
    logger = MyLogger()
    profect_dir = Path(__file__).resolve().parents[1]
    config_path = profect_dir / "config.yml"

    if not config_path.exists():
        generate_config_file(config_path)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    Path(config["output_dir"]).mkdir(exist_ok=True, parents=True)
    db_cliant = DatabaseCliant(Path(config["database_path"]))
    honto_cliant = HontoSearchCliant()
    ehon_cliant = EhonSearchCliant()

    # input_dir内のPDFに対して処理をする
    for pdf_file in Path(config["input_dir"]).glob("**/*.pdf"):
        try:
            book_info = fetch_book_info_from_pdf(pdf_file, honto_cliant, ehon_cliant)
        except NotFoundIsbnError as e:
            send_err_dir(pdf_file, Path(config["output_dir"]))
            logger.write("ERROR", str(e))
            continue
        except HontoDoesNotHaveDataError as e:
            send_err_dir(pdf_file, Path(config["output_dir"]))
            logger.write("ERROR", str(e))
            continue

        dst = construct_dst(config["output_dir"], book_info)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pdf_file), dst)
        logger.write("SUCCESS", dst)

        # データベースに情報を追加
        fetch_result = {
            "title": book_info["title"],
            "isbn": book_info["isbn"],
            "authors": "\t".join(book_info["authors"] or [""]),
            "publishers": book_info["publisher"],
            "categories": book_info["category"],
            "destination": str(dst)
        }

        db_cliant.store(fetch_result)
    db_cliant.close()


def parser() -> Namespace:
    """setting for argparser

    Returns:
        Namespace: args namespace.
    """
    usage = f"Usage: python {__file__}"
    argparser = ArgumentParser(usage=usage)
    args = argparser.parse_args()
    return args


if __name__ == "__main__":
    show_title()
    args = parser()
    main()
