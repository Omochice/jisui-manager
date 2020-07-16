import re

corpus = {z: str(h) for z, h in zip("０１２３４５６７８９", range(10))}

z2h = str.maketrans(corpus)    # 全角数字->半角数字のtranslaterを作成


def format_title(title: str) -> str:
    """入力文字列を整形する

    Args:
        title (str): タイトル文字列

    Returns:
        str: 整形した文字列
    """
    half_width = re.sub('[（）　:<>/="]', ' ', title).rstrip()
    half_width.translate({"?": "？", "!": "！"})
    return re.sub(' +', '_', half_width.translate(z2h))
