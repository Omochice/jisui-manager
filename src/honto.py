from typing import Optional

import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


class HontoSearchCliant:
    def __init__(self):
        self.url = "https://honto.jp/netstore/search.html"    # 紙+電子書籍の検索
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

    def _fetch_html(self, page_url: str, **kwargs) -> str:
        """requestsを短くするためのヘルパ関数"""
        r = requests.get(url=page_url, headers=self.user_agent, **kwargs,
                         verify=False).text
        return r

    def fetch_individual_page(self, isbn: str) -> BeautifulSoup:
        """入力されたISBNから個別の書籍ベージのhtmlデータを取得する"""
        # 検索する
        params = {
            "detailFlg": 1,
            "isbn": isbn,
            "seldt": r"2023%2Fall%2Fall%2Fbefore",
            "srchf": 1,
            "store": 1
        }

        # 検索結果から個別ページへいく
        soup = BeautifulSoup(self._fetch_html(self.url, params=params),
                             features="html.parser")
        individual_page_url = soup.find("a", class_="dyTitle").get(
            "href")    # 複数hitは戦闘のものを抽出

        soup = BeautifulSoup(self._fetch_html(individual_page_url),
                             features="html.parser")
        return soup

    def _get_topicpath(self, soup: BeautifulSoup) -> list:
        """ページ上部のトピックパスを取得するヘルパ関数"""
        return [t.text for t in soup.select("div#stTopicPath > ol > li")]

    def _get_category(self, soup: BeautifulSoup) -> str:
        """書籍の大分類を返す"""
        # "の通販"を外す
        category = self._get_topicpath(soup)[2].split("の通販")[0]
        return category

    def _get_sub_category(self, soup: BeautifulSoup, category: str) -> Optional[str]:
        """書籍の小分類を返す

        文庫 -> 著者名
        小説 -> 著者名
        漫画 -> シリーズ名
        ライトノベル -> シリーズ名
        新書 -> レーベル
        その他 -> サブ分類
        """
        if category in {"文庫", "小説・文学"}:
            author = [t.text for t in soup.select("p#stAuthor > span > a")][0]
            sub_category = author.split(":")[-1]    # 著:などの除去
        elif category in {"漫画・コミック", "ライトノベル"}:
            media = soup.select("p.stFormat")[0].contents[0]
            if media == "電子書籍":
                sub_category = self._get_topicpath(soup)[-2]
            else:
                sub_category = None
        elif category == "新書・選書・ブックレット":
            sub_category = self._get_topicpath(soup)[-2]
        else:
            sub_category = self._get_topicpath(soup)[3].split("の通販")[0]
        return sub_category

    def fetch_category_info(self, isbn: str) -> dict:
        soup = self.fetch_individual_page(isbn)
        category = self._get_category(soup)
        sub_category = self._get_sub_category(soup, category)
        return {"category": category, "sub_category": sub_category}


if __name__ == "__main__":
    cliant = HontoSearchCliant()
    print(cliant.fetch_category_info(isbn="4088725158"))
