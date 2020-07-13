import sqlite3
from pathlib import Path


class DatabaseCliant:
    def __init__(self, database_path: Path) -> None:
        """initialize

        Args:
            database_path (Path): データベースのpath
        """
        self.dst = database_path
        self.connection = sqlite3.connect(self.dst)
        self.connection.row_factory = sqlite3.Row

    def __del__(self) -> None:
        """connectionを切断する
        """
        self.connection.close()

    def run_by_file(self, path: Path) -> None:
        """SQLファイルを読み込み実行する

        Args:
            path (Path): sql文が書いてあるファイルのpath
        """
        c = self.connection.cursor()
        with open(path) as f:
            c.executescript(f.read())

    def store(self, data: dict) -> None:
        """書籍データをデータべースに格納する

        Args:
            data (dict): 書籍データのdict
        """
        c = self.connection.cursor()
        params = self._build_query_params(data)
        c.execute(
            "INSERT INTO books(title, isbn, publisher_id, author_id, category_id, destination) VALUES(?, ?, ?, ?, ?, ?)",
            params)
        self.connection.commit()

    def _build_query_params(self, data: dict) -> tuple:
        """別テーブルに分けた出版社、著者、カテゴリのidを取得し、整形する

        Args:
            data (dict): 書籍データのdict

        Returns:
            tuple: connection.cursor.executeに適用するtuple
        """
        outer_key = {"publishers": None, "authors": None, "categories": None}
        for tmp in outer_key.keys():
            outer_key[tmp] = self.select_individual_id(tmp, data[tmp])

        return (data["title"], data["isbn"], outer_key["publishers"],
                outer_key["authors"], outer_key["categories"], data["destination"])

    def select_individual_id(self, table: str, column: str) -> int:
        """別テーブルに分けたIDを取得する

        Args:
            table (str): 取得元のtable名
            column (str): 検索に使うcolumn名

        Returns:
            int: columnに対応するID
        """
        c = self.connection.cursor()
        base_query = f"SELECT id FROM {table} WHERE name=?"    # テーブル名に?を埋め込むことはできない
        columns_id = c.execute(base_query, (column, )).fetchone()
        if columns_id is None:
            c.execute(f"INSERT INTO {table}(name) VALUES(?)", (column, ))
            self.connection.commit()
            columns_id = c.execute(base_query, (column, )).fetchone()
        return columns_id["id"]


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parents[1]
    database = project_dir / "database.sqlite3"
    cliant = DatabaseCliant(database)
    cliant.store({
        "title": "test_title",
        "isbn": "test_isbn",
        "publishers": "test_pub",
        "authors": "hogehoge",
        "categories": "h",
        "destination": "gg"
    })
    # cliant.run_by_file(project_dir / "schema.sql")
    # print((cliant.select_individual_id("publisher", "fuga")))