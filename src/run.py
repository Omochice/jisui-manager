import csv
import os
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
    dst.mkdir(parents=True, exist_ok=True)
    shutil.move(str(target), dst)


def generate_config_file(config_path: Path) -> None:
    """configファイルがないときに生成を行う

    Args:
        config_path (Path): configファイルの置き場所
    """
    input_dir = Path("not exists path")    # dummy path

    item = ("input_dir", "output_dir", "database_path")
    config = {}

    print("Cannot find config file.")
    print("\tGenerating config file...")

    for i in item:
        directory = Path("not exist path")

        while True:
            print(f"\tInput {i}: ", end="")
            directory = Path(input()).resolve()
            if i == "input_dir" and not directory.exists():
                print("\tThe path is not exists...")
            else:
                print()
                break
        config[i] = str(directory)

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


def completion_no_isbn(source_csv_path: str) -> None:
    logger = MyLogger()
    honto = HontoSearchCliant()
    ehon = EhonSearchCliant()

    with open(Path(__file__).resolve().parents[1] / "config.yml") as f:
        config = yaml.safe_load(f)
        os.makedirs(config["output_dir"], exist_ok=True)

    db_cliant = DatabaseCliant(Path(config["database_path"]))

    csv_path = Path(source_csv_path).resolve()
    with open(csv_path) as f:
        reader = csv.reader(f)
    for row in reader:
        book_path = Path(row[0]).resolve()
        isbn = str(row[1])
        try:
            info = fetch_book_info_from_isbn(isbn, honto, ehon)
        except HontoDoesNotHaveDataError as e:
            send_err_dir(book_path, config["output_dir"])
            logger.write("ERROR", str(e))
            continue
        else:
            dst = construct_dst(config["output_dir"], info)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(book_path), dst)
            logger.write("SUCCESS", dst)

            # データベースに情報を追加
            fetch_result = {
                "title": info["title"],
                "isbn": info["isbn"],
                "authors": "\t".join(info["authors"] or [""]),
                "publishers": info["publisher"],
                "categories": info["category"],
                "destination": str(dst)
            }

            db_cliant.store(fetch_result)
    db_cliant.close()


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

    os.makedirs(config["output_dir"], exist_ok=True)
    db_cliant = DatabaseCliant(Path(config["database_path"]))
    honto_cliant = HontoSearchCliant()
    ehon_cliant = EhonSearchCliant()

    # input_dir内のPDFに対して処理をする
    for pdf_file in Path(config["input_dir"]).glob("**/*.pdf"):
        try:
            book_info = fetch_book_info_from_pdf(pdf_file, honto_cliant, ehon_cliant)
        except NotFoundIsbnError as e:
            send_err_dir(pdf_file, config["output_dir"])
            logger.write("ERROR", str(e))
            continue
        except HontoDoesNotHaveDataError as e:
            send_err_dir(pdf_file, config["output_dir"])
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
    usage = f"Usage: python {__file__} [-i input_csv]"
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument(
        "-i",
        "--input_csv",
        help=
        "If you want to manage no isbn having book too, specify csv path. like 'book_pash', 'isbn'"
    )

    args = argparser.parse_args()
    return args


if __name__ == "__main__":
    show_title()
    args = parser()
    if args.input_csv is None:
        main()
    else:
        completion_no_isbn(args.input_csv)
