# cat-hand

## Q.このコードを使用すると？

## A.特定のタイミングでサーバー内のメンバーを抽選するbotが作れます。

### 機能
* 毎週決まった日時に自動で抽選を行い、結果を送信します。
* `/add`, `/rm` コマンドで、抽選対象や抽選済みメンバーを手動で管理可能。
* 抽選結果は `data/zumi.txt` に保存され、重複当選を防ぎます。

### 環境構築

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

### .envの設定例

```python
TOKEN = 取得したトークン
CHID = チャンネルID
#抽選の日時
SCHEDULE_HOUR = 24時間表記
SCHEDULE_MINUTE = 
SCHEDULE_WEEKDAY = 曜日を指定 0=月曜日 から 6=日曜
```

### 実行

```python
python3 bot.py
```

### 使い方

| コマンド | 引数 | 説明 |
| :--- | :--- | :--- |
| **/help** | なし | Botの**コマンドの使い方**を表示します。 |
| **/ls** | なし | Botが管理している**リストの名前** (`zumi`, `kouho`) を表示します。|
| **/cat** | `[リスト名]` | 指定したリスト（**`zumi`** または **`kouho`**）の**中身**（メンバー名）を確認します。 |
| **/add** | `@メンション` (複数可) | 指定したユーザーを**未抽選リスト（候補: kouho）**に戻します。 |
| **/rm** | `@メンション` (複数可) | 指定したユーザーを**抽選済みリスト（除外: zumi）**に追加します。 |
| **`exe`** | なし | **手動で抽選**を実行し、結果を発表します。 |