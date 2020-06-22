import requests
import json
import re


class OpenDbSearchCliant:
    def fetch(self, isbn_code: str) -> dict:
        d = self._fetch(isbn_code)
        for serialized in self._serialize(d):
            yield serialized

    def _fetch(self, isbn_code: str) -> dict:
        URL = "https://api.openbd.jp/v1/get"
        params = {"isbn": isbn_code}
        r = json.loads(requests.get(URL, params=params).text)
        return r

    def _serialize(self, response: dict) -> dict:
        """レスポンスから必要な部分を抜き出す"""
        for r in response:
            summary = r["summary"]
            serialized = {
                "title": (title:=self._format_title(summary["tilte"])),
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

    isbn = "9784339029079"
    
    for r in OpenDbSearchCliant().fetch(isbn):
        print(r)
