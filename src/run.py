import os
import shutil
from pathlib import Path

import yaml

from databese import DatabaseCliant
from honto import HontoSearchCliant
from JpNdl import JpNdlSearchCliant
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
    shutil.move(path, dst)


def generate_config_file(config_path: Path) -> None:
    input_dir = Path("not exists path")

    print("Cannot find config file.")
    print("\tGenerating config file...")

    while not input_dir.exists():
        print("\tInput input directory: ", end="")
        input_dir = Path(input()).resolve()
        if not input_dir.exists():
            print("\tThe path is not exists...")

    print("\tInput output directory: ", end="")
    output_dir = Path(input()).resolve()

    config = {"input_dir": str(input_dir), "output_dir": str(output_dir)}

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, allow_unicode=True)


def main():
    logger = MyLogger()
    profect_dir = Path(__file__).resolve().parents[1]
    config_path = profect_dir / "config.yaml"

    if not config_path.exists():
        generate_config_file(config_path)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    os.makedirs(config["output_dir"], exist_ok=True)
    db_cliant = DatabaseCliant(config["database_path"])

    # input_dir内のPDFに対して処理をする
    for pdf_file in Path(config["input_dir"]).glob("**/*.pdf"):
        # isbnの取得
        isbn_code = scan_isbn(pdf_file)

        if isbn_code is None:
            send_err_dir(pdf_file, Path(config["output_dir"], "tmp"))
            logger.write("ERROR", "ISBN not found.")

        # 書籍情報の取得
        book_info = (
            OpenBDSearchCliant().fetch(isbn_code)    # 複数取得もあるけど最初の1個だけでいいと思う
            or JpNdlSearchCliant().fetch(isbn_code))

        if book_info is None:
            send_err_dir(pdf_file, Path(config["output_dir"], "tmp"))
            logger.write("ERROR", "Title not found.")
            # 書籍タイトルが取得できないとき(Hontoだと出版社名とかも入ってきて使いにくい)

        # カテゴリの取得
        categories = HontoSearchCliant().fetch_category_info(isbn_code)

        # リネームして移動
        dst = Path(config["output_dir"], categories["category"],
                   categories["sub_category"], book_info["title"] + ".pdf")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(pdf_file, dst)
        logger.write("SUCCESS", dst)

        # データベースに情報を追加
        fetch_result = {
            "title": book_info["title"],
            "isbn": isbn_code,
            "authors": "\t".join(book_info["authors"]),
            "publishers": book_info["publisher"],
            "categories": categories["category"],
            "destination": str(dst)
        }

        db_cliant.store(fetch_result)


if __name__ == "__main__":
    main()
    # show_title()
