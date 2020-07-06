# Book DB

## これはなに

これは自炊書籍の管理をちょっとだけ楽にできるかもしれないツールです。

## 使い方

1. Tesseractを使うのでaptとかで入れてください。
    ```sh
    $ sudo apt install tesseract-ocr
    $ sudo apt install libtesseract-dev
    ```
1. このツールをまるっとgitでcloneする
    ```sh 
    $ git clone https://github.com/Omochice/book_manager.git
    ```
1. 初回起動時(プロジェクト直下にconfigファイルがないとき)にpdfの入っているディレクトリと出力先のディレクトリを尋ねるので答える。
    ```sh
    $ cd book_manager
    $ python3 src/run.py
    [入力先と出力先を入力]
    ```
1. エラー終了しなければ指定した出力先にリネームしたpdfファイルがあるはずです。
   * ISBNが読み取れない、タイトルが取得できないなどの場合は`[出力先]/tmp`内に移動します

## 動作確認環境

Ubuntu 20.04 LTS


