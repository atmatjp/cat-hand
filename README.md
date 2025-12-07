# cat-hand

Q.このコードを使用すると？

A.特定のタイミングでサーバー内のメンバーを抽選するbotが作れます。毎週の当番決めなどにどうぞ。

## 機能
* 毎週決まった日時に自動で抽選を行い、結果を送信します。
* `/add`, `/rm` コマンドで、抽選ユーザを手動で管理可能。
* 抽選結果は `data/` ディレクトリに`.txt`形式で保存され、重複当選を防ぎます。

## 環境構築

Debian / Ubuntu系での構築例

```bash
sudo apt install python3
sudo apt install python3-venv
sudo apt install pip
git clone https://github.com/atmatjp/cat-hand
cd cat-hand
python3 -m venv venv
source venv/bin/activate
pip install discord.py python-dotenv
```

MacOSでの構築例

```bash
brew install git python
git clone https://github.com/atmatjp/cat-hand
cd cat-hand
python3 -m venv venv
source venv/bin/activate
pip install discord.py python-dotenv
```

## .envの設定例

```python
TOKEN = 取得したトークン
CHID = チャンネルID
#抽選の日時
SCHEDULE_HOUR = 
SCHEDULE_MINUTE = 
SCHEDULE_WEEKDAY = 曜日を指定 0=月曜日 から 6=日曜
```

## 実行

```python
python3 bot.py
```

## 使い方

| コマンド | 引数 | 説明 |
| :--- | :--- | :--- |
| **/help** | なし | Botのコマンドの使い方を表示します。 |
| **/ls** | なし | Botが管理しているリストの名前を表示します。|
| **/cat** | `/リスト名` | 指定したリストの中身を確認できます。 |
| **/add** | `@メンション`(複数可) `ユーザ名`(複数可)| 指定した対象を未抽選リストに戻します。 |
| **/rm** | `@メンション`(複数可) `ユーザ名`(複数可)| 指定した対象を抽選済みリストに追加します。 |
| **`pick`** | なし | 手動で抽選を実行し、結果を発表します。 |