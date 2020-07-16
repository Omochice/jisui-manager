import os
import shutil
from pathlib import Path

import yaml

from databese import DatabaseCliant
from honto import HontoSearchCliant
from JpNdl import JpNdlSearchCliant
from google_book import GoogleBookSearchCliant
from mylogger import MyLogger
from openbd import OpenBDSearchCliant
from scan_isbn import scan_isbn


def show_title():
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


def send_err_dir(path: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), dst)


def generate_config_file(config_path: Path) -> None:
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

    # input_dir内のPDFに対して処理をする
    for pdf_file in Path(config["input_dir"]).glob("**/*.pdf"):
        print(str(pdf_file))
        # isbnの取得
        isbn_code = scan_isbn(pdf_file)

        if isbn_code is None:
            send_err_dir(pdf_file, Path(config["output_dir"], "tmp"))
            logger.write("ERROR", f"ISBN not found. {pdf_file.name}")
            continue

        print(isbn_code)
        # 書籍情報の取得
        # book_info = (OpenBDSearchCliant().fetch(isbn_code)
        #              or GoogleBookSearchCliant().fetch(isbn_code)
        #              or JpNdlSearchCliant().fetch(isbn_code))
        honto_cliant = HontoSearchCliant()
        try:
            book_info = honto_cliant.fetch_book_info(isbn_code)
        except ValueError as e:
            logger.write("ERROR",
                         f"honto.jp not have the page. {isbn_code=}. {pdf_file.name}")
        # if book_info is None:
        #     send_err_dir(pdf_file, Path(config["output_dir"], "tmp"))
        #     logger.write("ERROR", f"Title not found. {pdf_file.name}")
        #     continue
        #     # 書籍タイトルが取得できないとき(Hontoだと出版社名とかも入ってきて使いにくい)

        # # カテゴリの取得
        # try:
        #     categories = HontoSearchCliant().fetch_category_info(isbn_code)
        # except ValueError:
        #     send_err_dir(pdf_file, Path(config["output_dir"], "tmp"))
        #     logger.write("ERROR", f"Category not found. {pdf_file.name}")
        #     continue

        # リネームして移動
        # dst = Path(config["output_dir"], categories["category"],
        #            categories["sub_category"] or "", book_info["title"] + ".pdf")
        dst = Path(config["output_dir"], book_info["category"],
                   book_info["sub_category"] or "", book_info["title"] + ".pdf")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pdf_file), dst)
        logger.write("SUCCESS", dst)

        # データベースに情報を追加
        fetch_result = {
            "title": book_info["title"],
            "isbn": isbn_code,
            "authors": "\t".join(book_info["authors"] or [""]),
            "publishers": book_info["publisher"],
            "categories": book_info["category"],
            "destination": str(dst)
        }

        db_cliant.store(fetch_result)
    db_cliant.close()


if __name__ == "__main__":
    main()
    # show_title()
