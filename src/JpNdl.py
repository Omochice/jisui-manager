from typing import Optional

import requests
import xmltodict


class JpNdlSearchCliant:
    """国会図書館APIを叩くためのrequestラッパー"""
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._response = None

        self._allow_dh1024()

    def _allow_dh1024(self) -> None:
        """1024bitの鍵帳を許可する"""
        # 拾ってきたやつだからセキュリティがあれかもしれない
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
        try:
            requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
        except AttributeError:
            # no pyopenssl support used / needed / available
            pass

    def fetch(self, isbn: str) -> Optional[dict]:
        """[summary]

        Args:
            isbn (str): isbn 13 or 10

        Returns:
            Optional[dict]: 書籍情報が得られればdict, そうでなければNone
        """
        base_url = f"http://iss.ndl.go.jp/api/sru?operation=searchRetrieve&query=isbn={isbn}"    # =を2つ埋め込むのどうやるん
        self._response = requests.get(base_url)
        return self._serialize()

    def _serialize(self) -> Optional[dict]:
        """APIから得た情報を読みやすくする

        Returns:
            Optional[dict]: xmlを変換して読みやすくしたdict, APIのレコードがなければNone
        """
        book_info = self._xml2dict()

        if book_info is None:
            return None
        else:
            return {
                "title": book_info.get("dc:title", None),
                "author": book_info.get("dc:aushor", None),
                "publisher": book_info.get("dc:publisher", None)
            }

    def _xml2dict(self) -> Optional[dict]:
        """xmlをdict形式へ変換する

        Returns:
            Optional[dict]: 変換結果のdict, レコード数が0ならNoneを返す
        """
        records = xmltodict.parse(self._response.text)

        if records["searchRetrieveResponse"]["numberOfRecords"] == 0:
            return None
        else:
            dc_records = records["searchRetrieveResponse"]["records"]["record"]
            book_info = xmltodict.parse(
                dc_records[0]["recordData"])["srw_dc:dc"]    # 先頭のみ使う
            return book_info


if __name__ == "__main__":
    test_isbn = "978-4839970253"
    print(JpNdlSearchCliant().fetch(isbn=test_isbn))
    # print(res)
