import requests
import json
from bs4 import BeautifulSoup
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


class HontoSearchCliant:
    def __init__(self):
        self.url = "https://honto.jp/netstore/search_021.html"    # 紙の本の検索
        self.user_agent = {
            "user-agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.98 Safari/537.36"
        }
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

    def fetch_html(self, page_url: str, **kwargs) -> str:
        r = requests.get(url=page_url, headers=self.user_agent, **kwargs,
                         verify=False).text
        return r

    def fetch_category(self, isbn: str) -> str:
        # 検索する
        params = {
            "detailFlg": 1,
            "isbn": isbn,
            "seldt": r"2023%2Fall%2Fall%2Fbefore",
            "srchf": 1,
            "store": 1
        }

        # 検索結果から個別ページへいく
        soup = BeautifulSoup(self.fetch_html(self.url, params=params),
                             features="html.parser")
        individual_page = soup.find("a", class_="dyTitle").get("href")

        # カテゴリを取得
        soup = BeautifulSoup(self.fetch_html(individual_page), features="html.parser")
        # "の通販"を外す
        category = [t.text for t in soup.select("div#stTopicPath > ol > li")][2][:-3]
        return category


if __name__ == "__main__":
    aliant = HontoSearchCliant()
    print(aliant.fetch_category(isbn="9784339029079"))