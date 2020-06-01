import json
import subprocess

import xmltodict


class CalibreBookInformation:
    """Calibreを使って入手したデータをまとめたクラス"""
    def __init__(self,
                 title: str = None,
                 authors: str = None,
                 publisher: str = None,
                 publish_day: str = None,
                 identifier: dict = None,
                 description: str = None,
                 series_title: str = None,
                 series_index: int = None):
        self.title = title
        self.authors = authors
        self.publisher = publisher
        self.publish_day = publish_day
        self.identifier = identifier
        self.description = description
        self.series_title = series_title
        self.series_index = series_index

        self.information = {
            "title": self.title,
            "authors": self.authors,
            "publisher": self.publisher,
            "identifier": self.identifier,
            "description": self.description,
            "series_title" : self.series_title,
            "series_index" : self.series_index
        }

    def __str__(self):
        return json.dumps(self.information, indent=4, ensure_ascii=False)


class CalibreClient:
    def __init__(self):
        pass

    def fetch_information(self,
                          title: str = None,
                          authors: list = None,
                          isbn: str = None) -> CalibreBookInformation:
        """command lineでcalibreのツールを使い、情報を取得する
        
        Parameters
        ----------
        title: str
            書籍の名前
        authors: list
            著者名
        isbn: str
            ISBNコード

        Outputs
        ----------
        CalibreBookInformation: CalibreBookInformation
            取得した情報
        """
        # コマンドクエリの作成
        query_base = ["fetch-ebook-metadata", "--opf"]
        if title is not None:
            query_base.extend(["--title", title])
        elif authors is not None:
            query_base.extend(["--authors", authors])
        elif isbn is not None:
            query_base.extend(["--isbn", isbn])
        else:
            raise ValueError("You must specify at least one of title, authors or ISBN.")

        # サブプロセスでコマンドを実行
        cp = subprocess.run(query_base,
                            encoding="UTF-8",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        if cp.returncode != 0:
            return None
        else:
            return CalibreBookInformation(**self._seliarize(self._xml2dict(cp.stdout)))

    def _xml2dict(self, rst: str) -> dict:
        return xmltodict.parse(rst)

    def _seliarize(self, dubline_core: dict) -> dict:
        """ダブリンコア形式で与えられたデータから主要情報を直列化する

        Parameters
        ----------
        dubline_core: dict
            ダブリンコア形式のdictデータ

        Outputs
        ----------
        selialized_metadata: dict
            直列化されたデータ
        """

        metadata = dubline_core["package"]["metadata"]

        creators = metadata["dc:creator"]
        if type(creators) is not list:    # 著者が複数人のフォーマットに合わせる
            creators = [creators]

        series_info = self.get_series(dubline_core)

        selialized_metadata = {
            "title": metadata["dc:title"],
            "authors": [author["#text"] for author in creators],
            "publisher": metadata["dc:publisher"],
            "publish_day": metadata["dc:date"],
            "identifier": {
                dc_identifier["@opf:scheme"]: dc_identifier["#text"]
                for dc_identifier in metadata["dc:identifier"]
            },
            "description": metadata["dc:description"],
            "series_title": series_info[0],
            "series_index": series_info[1]
        }
        return selialized_metadata



    def get_series(self, dubline_core: dict) -> tuple:
        """ダブリンコア形式のデータからシリーズ情報を入手する

        Parameters
        ----------
        dubline_core: dict
            dict化されたダブリンコア形式のデータ

        Outputs
        ----------
        (series_title, series_index): tuple
            シリーズの名称と何巻かの情報。
            シリーズものでなければ(None, None)を返す。
        """
        #[TODO] 日本語以外も取得してるのをなんとかする
        #[TODO] シリーズの取得ができないものが多いのをなんとかする
        series_title = None
        series_index = None
        meta = dubline_core["package"]["metadata"].get("meta", None)
        if meta is None:
            return (series_title, series_index)
        else:
            if type(meta) is not list:
                meta = [meta]
            for meta_dict in meta:
                if "calibre:series" in (v:=meta_dict.values()):
                    series_title = meta_dict["@content"]
                elif "calibre:series_index" in v:
                    series_index = meta_dict["@content"]
        return (series_title, series_index)
    


if __name__ == "__main__":
    # test_name = "退屈なことはＰｙｔｈｏｎにやらせよう"
    test_name = "涼宮ハルヒの憤慨"
    isbn_code = "4088725158"
    cliant = CalibreClient()
    # print(cliant.fetch_information(title=test_name))
    print(cliant.fetch_information(isbn=isbn_code))
