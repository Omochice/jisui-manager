from datetime import datetime
from pathlib import Path
from typing import Union


class MyLogger:
    """入力されたファイルと処理結果を書く簡単なロガーのクラス
    """
    def __init__(self) -> None:
        """logファイルをプロジェクト直下に作成する
        """
        logger_path = Path(__file__).resolve().parents[1] / "book_db.log"
        logger_path.touch()
        self.fp = open(logger_path, "a")

    def __del__(self):
        """closeは忘れずにする
        """
        self.fp.close()

    def write(self, status: str, operand: Union[Path, str]):
        """['時刻', '処理ステータス', '情報']をtsvライクな形式で書き込む

        Args:
            status (str): "SUCCESS" or "ERROR"
            operand (Union[Path, str]): SUCCESSなら移動先のパス文字列, ERRORならどこでのエラーなのか
        """
        row = "\t".join([datetime.now().strftime("%Y-%m-%d %R"), status, str(operand)])
        print(row, file=self.fp)
