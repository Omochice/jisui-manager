import sqlite3
import yaml
from pathlib import Path


def generate_config_file(config_path: Path) -> None:
    input_dir = Path("not exists path")

    print("Cannot find config file.")
    print("\tGenerating config file...")

    while not input_dir.exists():
        print("\tInput input directory: ", end="")
        input_dir = Path(input()).resolve()
        if not input_dir.exists():
            print("\tThe path is not exists...")

    print("\tInput output directory: ", end="")
    output_dir = Path(input()).resolve()

    config = {"input_dir": str(input_dir), "output_dir": str(output_dir)}

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, allow_unicode=True)


def main():
    profect_dir = Path(__file__).resolve().parents[1]
    config_path = profect_dir / "config.yaml"

    if not config_path.exists():
        generate_config_file(config_path)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # input_dir内のPDFに対して処理をする
    for pdf_file in Path(config["input_dir"]).glob("**/*.pdf"):
        # isbnの取得
        # 書籍情報の取得
        #　カテゴリの取得
        # リネームして移動
        # データベースに情報を追加
        pass


if __name__ == "__main__":
    main()