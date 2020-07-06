import json
import re
from typing import Optional, Iterator, Union

import requests


class OpenBDSearchCliant:
    """OpenBDのAPIを叩くクラス
    """
    def __init__(self):
        self.user_agent = {
            "user-agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.98 Safari/537.36"
        }
        self.response = None

    def fetch(self,
              isbn_code: str,
              use_first: bool = True) -> Optional[Union[dict, list]]:
        """OpenBDのAPIを叩いて書籍情報をdictで取得する

        Args:
            isbn_code (str): ISBNコード
            use_first (bool, optional): 複数結果のうち最初の1件のみを返すかどうか. Defaults to True.

        Returns:
            Optional[Union[dict, list]]: 書籍情報のdict(use_firstがTrueならlist[dict])
        """
        URL = "https://api.openbd.jp/v1/get"
        params = {"isbn": isbn_code}
        self.response = requests.get(URL, params=params, headers=self.user_agent)
        r = json.loads(self.response.text)

        if not any(r):    # [None]だったら
            return None

        serialized = list(self._serialize(r))
        if use_first:
            # 特に指定がなければレコードの先頭を返す
            return serialized[0]
        else:
            return serialized

    def _serialize(self, response: dict) -> Iterator[dict]:
        """レスポンスから必要な部分を抜き出す

        Args:
            response (dict): jsonレスポンスをdictにしたもの

        Yields:
            Iterator[dict]: 必要な部分を抜き出したdictを返すイテレータ
        """
        for r in response:
            summary = r["summary"]
            serialized = {
                "title": (self._format_title(summary["title"])),
                "identifier": {
                    "isbn": summary["isbn"]
                },
                "authors": self._fotmat_authors(summary["author"]),
                "publisher": summary["publisher"]
            }
            yield serialized

    def _format_title(self, title: str) -> str:
        """カッコなどを半角スペース一個に置き換える"""
        half_width = re.sub('[（）　]', ' ', title).rstrip()
        return re.sub(' +', ' ', half_width)

    def _fotmat_authors(self, authors: str) -> list:
        """著者名をリストにする

        hoge／foo piyo/bar -> [hoge, piyo]
        """
        return list(map(lambda x: re.sub(r"／.+", "", x), authors.split(" ")))


if __name__ == "__main__":

    # isbn = "9784339029079"
    isbn = "9784780802047"
    # isbn = "9784040800202"
    print(isbn)

    print(OpenBDSearchCliant().fetch(isbn))
    # for r in OpenDbSearchCliant().fetch(isbn):
    # print(r)
