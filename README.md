# Book DB

## これはなに

これは自炊書籍の管理をちょっとだけ楽にできるかもしれないツールです。

## 使い方

1. Tesseractを使うのでaptとかで入れてください。
    * Ubuntu(Debian)
        ```sh
        $ sudo apt install tesseract-ocr libtesseract-dev
        ```
    * Manjaro(Arch)
        ```sh
        $ sudo pacman -S tesseract tessetact-data-eng
        ```
2. このツールをまるっとgitでcloneする
    ```sh 
    $ git clone https://github.com/Omochice/jisui-manager.git
    ```
3. 環境再現をする
    ```sh
    $ pip install pipenv
    $ cd jisui-manager
    $ pipenv install
    ```
4. 初回起動時(プロジェクト直下にconfigファイルがないとき)にpdfの入っているディレクトリと出力先のディレクトリを尋ねるので答える。
    ```sh
    $ cd  jisui-manager
    $ pipenv run start
    [入力先と出力先を入力]
    ```
5. エラー終了しなければ指定した出力先にリネームしたpdfファイルがあるはずです。
   * ISBNが読み取れない、タイトルが取得できないなどの場合は`[出力先]/tmp`内に移動します

## 動作確認環境

Ubuntu 20.04 LTS
Manjaro Linux


