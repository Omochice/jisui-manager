import re

corpus = {
    **{z: str(h)
       for z, h in zip("０１２３４５６７８９", range(10))},
    **{chr(ord("Ａ") + i): chr(ord("A") + i)
       for i in range(26)},
    **{chr(ord("ａ") + i): chr(ord("a") + i)
       for i in range(26)}
}
c_operator = {"?": "？", "!": "！"}    # !や?はパスに入ると演算子と認識される
z2h = str.maketrans(corpus)    # 全角数字->半角数字のtranslaterを作成
safe_operator = str.maketrans(c_operator)


def format_title(title: str) -> str:
    """入力文字列を整形する

    Args:
        title (str): タイトル文字列

    Returns:
        str: 整形した文字列
    """
    half_width = re.sub('[（）　:<>/="]', ' ', title).rstrip()
    half_width.translate(safe_operator)
    return re.sub(' +', '_', half_width.translate(z2h))


def format_authors(authors: list) -> list:
    formatted = [re.split("[:：]", author) for author in authors]
    formatted = [re.sub(r"[\(（].+?[\)）]", "", author) for author in authors]
    return [f.translate(z2h) for f in formatted]


def format_publisher(publisher: str) -> str:
    formatted = "goo"
    return formatted


if __name__ == "__main__":
    print(corpus)
    print(format_authors(["西尾章治郎(監修)", "原隆浩（著）", "水田智史（著）", "大川剛直（著）"]))
