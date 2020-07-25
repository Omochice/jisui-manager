import re
import csv
import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

import yaml

from databese import DatabaseCliant
from ehon import EhonSearchCliant
from honto import HontoDoesNotHaveDataError, HontoSearchCliant
from mylogger import MyLogger
from run import construct_dst, fetch_book_info_from_isbn, send_err_dir


def completion_no_isbn(source_csv_path: str) -> None:
    """手作業でisbnや移動先を書いたcsvを元に補完作業をする

    Args:
        source_csv_path (str): ソースとなるcsv
    """
    logger = MyLogger()
    honto = HontoSearchCliant()
    ehon = EhonSearchCliant()

    with open(Path(__file__).resolve().parents[1] / "config.yml") as f:
        config = yaml.safe_load(f)
        Path(config["output_dir"]).resolve().mkdir(exist_ok=True, parents=True)

    db_cliant = DatabaseCliant(Path(config["database_path"]))

    csv_path = Path(source_csv_path).resolve()
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            book_path = Path(row[0]).resolve()
            neemock = str(row[1])
            if re.fullmatch(r"[0-9-]+", neemock):
                isbn = neemock
                try:
                    store_specified_isbn(book_path, isbn, honto, ehon, config, logger,
                                         db_cliant)
                except HontoDoesNotHaveDataError as e:
                    send_err_dir(book_path, Path(config["output_dir"]))
                    logger.write("ERROR", str(e))
            else:
                dst = Path(neemock)
                db_cliant.update_dst(book_path, dst)
                shutil.move(str(book_path), str(dst / book_path.name))

    db_cliant.close()


def store_specified_isbn(target: Path, isbn: str, honto: HontoSearchCliant,
                         ehon: EhonSearchCliant, config: dict, logger: MyLogger,
                         db: DatabaseCliant) -> None:
    """isbnを元に元情報を上書きし、移動する

    Args:
        target (Path): 対象書籍のpath
        isbn (str): isbn
        honto (HontoSearchCliant): Hontoの検索クライアント
        ehon (EhonSearchCliant): E-honの検索クライアント
        config (dict): configのdict
        logger (MyLogger): logger
        db (DatabaseCliant): データベースのクライアント

    Raises:
        HontoDoesNotHaveDataError: Hontoがその書籍のページを持っていないときのエラー
    """
    try:
        info = fetch_book_info_from_isbn(isbn, honto, ehon)
    except HontoDoesNotHaveDataError as e:
        send_err_dir(target, Path(config["output_dir"]))
        logger.write("ERROR", str(e))
        raise HontoDoesNotHaveDataError(e)
    else:
        dst = construct_dst(config["output_dir"], info)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), dst)
        logger.write("SUCCESS", str(dst))

        # データベースに情報を追加
        fetch_result = {
            "title": info["title"],
            "isbn": info["isbn"],
            "authors": "\t".join(info["authors"] or [""]),
            "publishers": info["publisher"],
            "categories": info["category"],
            "destination": str(dst)
        }

        db.store(fetch_result)


def parser() -> Namespace:
    usage = f"python3 {__file__} [-i input_csv]"
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument("-i",
                           "--input",
                           help="Source csv file's path.",
                           required=True)
    args = argparser.parse_args()
    return args


if __name__ == "__main__":
    args = parser()
    completion_no_isbn(args.input)
