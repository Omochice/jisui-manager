import subprocess
import time

from bs4 import BeautifulSoup
from selenium import webdriver

import bookinfo_util


class EhonSearchCliant:
    def __init__(self) -> None:
        self.url = "https://www.e-hon.ne.jp/bec/SA/Search"
        self._driver_path = subprocess.run(["which", "chromium.chromedriver"],
                                           encoding="UTF-8",
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE).stdout.rstrip()
        self._options = webdriver.ChromeOptions()
        self._options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
        )
        self._options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self._options,
                                       executable_path=self._driver_path)

    def fetch_individual_page(self, isbn: str) -> BeautifulSoup:
        """入力されたISBNから個別の書籍ベージのhtmlデータを取得する

        Args:
            isbn (str): isbn code

        Returns:
            BeautifulSoup: 個別ページのHTMLを格納したBeautifulSoup
        """
        self.driver.get(self.url)
        self.driver.find_element_by_name("isbn").clear()
        self.driver.find_element_by_name("isbn").send_keys(isbn)
        self.driver.find_element_by_name("submitLabel").click()
        time.sleep(2)    # 念の為ページ遷移の時間を確保
        return BeautifulSoup(self.driver.page_source, "html.parser")

    def fetch_book_info(self, isbn: str) -> dict:
        """書籍情報を取得する

        Args:
            isbn (str): 調べる本のISBN

        Returns:
            dict: 書籍情報
        """
        soup = self.fetch_individual_page(isbn)
        title = soup.find("p", class_="itemTitle").text
        authors = soup.select("ul.AuthorsName > li > a")[0].text
        publisher = ""
        series_name = ""
        main_item_table = soup.select("div.mainItemTable > table > tbody > tr")
        for row in main_item_table:
            th = row.find("th").text
            td = row.find("td").text
            if th == "出版社名":
                publisher = td
            elif th == "シリーズ名":
                series_name = td
        info = {
            "title": bookinfo_util.format_title(title),
            "authors": authors,
            "publisher": bookinfo_util.format_publisher(publisher),
            "series_name": bookinfo_util.format_title(series_name)
        }
        return info

    def fetch_series_name(self, isbn: str) -> str:
        """シリーズ情報を取得する

        Args:
            isbn (str): 対象の本のisbn

        Raises:
            EhonDoesNotHaveDataError: E-honがその書籍のシリーズ情報を持っていないときのエラー

        Returns:
            str: シリーズ名
        """
        soup = self.fetch_individual_page(isbn)
        main_item_table = soup.select("div.mainItemTable > table > tbody > tr")
        series_name = None
        for row in main_item_table:
            th = row.find("th").text
            td = row.find("td").text
            if th == "シリーズ名":
                series_name = td
        if series_name is None:
            raise EhonDoesNotHaveDataError(
                f"e-hon.ne.jp have not get the series information. {isbn=}")
        else:
            return bookinfo_util.format_title(series_name)


class EhonDoesNotHaveDataError(Exception):
    pass


if __name__ == "__main__":
    # isbn = "9784894906396"
    isbn = "9784894906358"
    cliant = EhonSearchCliant()
    # print(cliant.fetch_book_info(isbn))
    print(cliant.fetch_series_name(isbn))
