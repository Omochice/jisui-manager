import xmltodict
import subprocess
import json


class CalibreBookInformation:
    def __init__(self,
                 title: str = None,
                 authors: str = None,
                 publisher: str = None,
                 publish_day: str = None,
                 identifier: dict = None,
                 description: str = None):
        self.title = title
        self.authors = authors
        self.publisher = publisher
        self.publish_day = publish_day
        self.identifier = identifier
        self.description = description

        self.information = {
            "title": self.title,
            "authors": self.authors,
            "publisher": self.publisher,
            "identifier": self.identifier,
            "description": self.description
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
            return CalibreBookInformation(**self._seliarize(cp.stdout))

    def _seliarize(self, rst: str) -> dict:
        dubline_core = xmltodict.parse(rst)
        metadata = dubline_core["package"]["metadata"]

        selialized_metadata = {
            "title": metadata["dc:title"],
            "authors": [author["#text"] for author in metadata["dc:creator"]],
            "publisher": metadata["dc:publisher"],
            "publish_day": metadata["dc:date"],
            "identifier": {
                dc_identifier["@opf:scheme"]: dc_identifier["#text"]
                for dc_identifier in metadata["dc:identifier"]
            },
            "description": metadata["dc:description"]
        }
        return selialized_metadata


if __name__ == "__main__":
    test_name = "データマイニングエンジニアの教科書"
    cliant = CalibreClient()
    print(cliant.fetch_information(title=test_name))