import unittest

from src import bookinfo_util


class TestBookinfoUtil(unittest.TestCase):
    def test_format_title(self):
        def helper(expected: str, actual: str):
            self.assertEqual(expected, bookinfo_util.format_title(actual))

        # 前括弧の削除
        helper("hoge", "【hoge】hoge")
        # 後括弧の削除
        helper("hoge", "hoge【hoge】")
        # 空白の置換
        helper("hoge", " hoge")
        helper("hoge", "　hoge")
        helper("hoge", "hoge ")
        helper("hoge", "hoge　")
        helper("hoge_hoge", "hoge hoge")

    def test_format_authors(self):
        def helper(expected: list, actual: list):
            self.assertEqual(expected, bookinfo_util.format_authors(actual))

        # 空白削除
        helper(["hoge", "foobar"], ["hog e", "foo bar"])
        # (著)などの削除
        helper(["foo", "bar"], ["foo(foo)", "bar（bar）"])

    def test_format_publisher(self):
        def helper(expected: str, actual: str):
            self.assertEqual(expected, bookinfo_util.format_publisher(actual))

        # 中点の削除
        helper("hoge", "ho・ge")
