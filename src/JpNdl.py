import xmltodict
import requests
from typing import Optional


class JpNdlSearchCliant:
    """国会図書館APIを叩くためのrequestラッパー"""
    def __init__(self, **kwargs):
        self._kwargs = kwargs
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

    def serch_by_isbn(self, isbn_code):
        """isbnコードで国会図書館APIを叩く
        
        Parameters
        ----------
        isbn_code: str
            13桁、または10桁のコード
        
        Returns
        -------
        book_information: JpNdlResponse
            xmlをパース
        """
        # isbnのみでの検索しか考慮してない
        base_url = f"http://iss.ndl.go.jp/api/sru?operation=searchRetrieve&query=isbn={isbn_code}"
        # params = {
        #     "operation": "searchRetrieve",
        #     "query": f"isbn={isbn_code}"
        # }    # query=isbn=<>の書き方がわからない
        r = requests.get(base_url)
        return JpNdlResponse(r)


class JpNdlResponse:
    """国会図書館APIのレスポンス
    """
    def __init__(self, response: requests.Response, isbn_code: str = None):
        self._title = None
        self._author = None
        self._publisher = None
        self._description = None
        self._publication_date = None
        self._response = response
        self.isbn = isbn_code

        self.serialize()

    def serialize(self) -> None:
        """得られたrequestの結果をシリアライズする"""
        book_info = self.xml2dict()

        def _serialize_helper(query: str) -> Optional[str]:
            if query in book_info:
                return book_info[query]
            else:
                return None

        self._title = _serialize_helper("dc:title")
        self._author = _serialize_helper("dc:author")
        self._publisher = _serialize_helper("dc:publisher")
        self._description = _serialize_helper("dc:descroption")

    def xml2dict(self) -> dict:
        """xmlをdict形式へ変換する"""
        dubline_core_style_records = xmltodict.parse(
            self._response.text)["searchRetrieveResponse"]["records"]["record"]
        book_info = xmltodict.parse(
            dubline_core_style_records[0]["recordData"])["srw_dc:dc"]
        return book_info

    def to_json(self) -> dict:
        """jsonとして吐き出す"""
        # jsondumpsまでする？
        return {
            "title": self._title,
            "author": self._author,
            "publisher": self._publisher,
            "descroption": self._description
        }


if __name__ == "__main__":
    test_isbn = "4774176982"
    cliant = JpNdlSearch()
    res = cliant.serch_by_isbn(isbn_code=test_isbn)

    print(res.to_json())
