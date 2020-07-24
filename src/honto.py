import json
import re
from typing import Optional

import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

import bookinfo_util

urllib3.disable_warnings(InsecureRequestWarning)


class HontoSearchCliant:
    def __init__(self) -> None:
        self.extended_url = "https://honto.jp/netstore/search.html"    # 紙+電子書籍の検索
        self.url = "https://honto.jp/netstore/search_022.html"    # 電子書籍のみ
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
        dytitle = soup.find("a", class_="dyTitle")

        if dytitle is None:
            dytitle = BeautifulSoup(self._fetch_html(self.extended_url, params=params),
                                    features="html.parser").find("a", class_="dyTitle")
            # 電子書籍のみでヒットしなければ紙も検索に含める
        if dytitle is None:    #それでもヒットしなければ
            raise HontoDoesNotHaveDataError(f"Honto not have the book data. {isbn=}")

        individual_page_url = dytitle.get("href")    # 複数hitは先頭のものを抽出

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
            author = ([
                t.text.split(":")[-1]
                for t in soup.find("p", class_="stAuthor").find_all("a")
            ] or [""])[0]
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
        """isbnを受け取りその本のカテゴリを返す

        Args:
            isbn (str): isbn番号

        Raises:
            HontoDoesNotHaveDataError: honto.jpにその本のページがないときのエラー

        Returns:
            dict: 大カテゴリ(漫画、新書など)と小カテゴリ(出版社など)のdict
        """
        try:
            soup = self.fetch_individual_page(isbn)
        except HontoDoesNotHaveDataError as e:
            raise HontoDoesNotHaveDataError(e)
        category = self._get_category(soup)
        sub_category = self._get_sub_category(soup, category)
        return {"category": category, "sub_category": sub_category}

    def fetch_book_info(self, isbn: str) -> dict:
        """書籍情報を返す

        Args:
            isbn (str): isbn

        Raises:
            HontoDoesNotHaveDataError: honto.jpにその本のページがないときのエラー

        Returns:
            dict: 書籍情報のdict
        """
        try:
            soup = self.fetch_individual_page(isbn)
        except HontoDoesNotHaveDataError as e:
            raise HontoDoesNotHaveDataError(e)

        script = soup.find_all("script", attrs={"type":
                                                "application/ld+json"})[1].string
        formatted = re.sub("　", " ", re.sub("[\n\r]", "", script))
        d = json.loads(formatted)

        #【.+】の削除
        book_title = re.search(r"(【.+】)?(.+)?(【.+】)?",
                               bookinfo_util.format_title(d["name"])).group(2)
        authors = [
            re.split(r"[:：]", t.text)[-1]
            for t in soup.find("p", class_="stAuthor").find_all("a")
        ] or [""]
        authors = [re.sub(" ", "", re.sub(r"\(.+\)", "", a)) for a in authors]
        publisher = d.get("brand", {}).get("name", "")
        category = self._get_category(soup)
        sub_category = self._get_sub_category(soup, category)

        info = {
            "title": book_title,
            "authors": bookinfo_util.format_authors(authors),
            "publisher": publisher,
            "category": category,
            "sub_category": sub_category
        }
        return info


class HontoDoesNotHaveDataError(Exception):
    pass


if __name__ == "__main__":
    cliant = HontoSearchCliant()
    print(cliant.fetch_book_info(isbn="9784047261273"))
