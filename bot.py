import discord
import random
import os
from dotenv import load_dotenv
from discord.ext import tasks
import datetime

#.envファイルからTOKENを読み込む
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHID = os.getenv("CHANNEL_ID")

#自動抽選の結果を送信するチャンネルID
#IDが数字かどうかチェックして変換
CHANNEL_ID = int(CHID) if CHID and CHID.isdigit() else None

#Discordに接続するための設定
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  
client = discord.Client(intents=intents)

DATA_FILE = "./data/zumi.txt"
zumi = []
#日本標準時
JST = datetime.timezone(datetime.timedelta(hours=9))

#データをファイルに保存する関数
def save_data():
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            for user_id in zumi:
                f.write(str(user_id) + '\n')
        print("データを外部ファイルに格納しました。")
    except Exception as e:
        print(f"格納に失敗: {e}")

#データをファイルから読み込む関数
def load_data():
    global zumi
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                zumi = [int(line.strip()) for line in f.readlines()]
            print(f"変数格納ファイルを読み込みました。現在の除外人数: {len(zumi)}人")
        except Exception as e:
            print(f"外部にある変数格納ファイルの読み込みに失敗しました: {e}")
    else:
        print("新規スタート")

# メンバー検索用ヘルパー関数（メンションと名前の両方に対応）
def get_targets(message, args, server):
    targets = []
    # 1. まずメンションされた人を確保
    if message.mentions:
        targets.extend(message.mentions)
    
    # 2. テキストで指定された名前も探す
    # args[1:] はコマンド(/addなど)を除いた部分
    name_list = args[1:]
    for name_str in name_list:
        # すでにメンションで取得済みの文字列（<@123..>）はスキップ
        if name_str.startswith('<@') and name_str.endswith('>'):
            continue
        
        # 名前でメンバーを探す
        found_member = discord.utils.find(lambda m: m.display_name == name_str or m.name == name_str, server.members)
        
        # 見つかった、かつ まだリストに入っていないなら追加
        if found_member and found_member not in targets:
            targets.append(found_member)
            
    return targets

#定期実行タスク
@tasks.loop(time=datetime.time(hour=10, minute=45, tzinfo=JST))
async def weekly_lottery_task():
    now_jst = datetime.datetime.now(JST)
    if now_jst.weekday() == 4:
        if not CHANNEL_ID:
            print("チャンネルIDが設定されていません。")
            return
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print(f"エラー: チャンネルID {CHANNEL_ID} が見つかりません。")
            return
        server = channel.guild
        zenin = [m for m in server.members if not m.bot]
        kouho = [m for m in zenin if m.id not in zumi]
        if not kouho:
            await channel.send("【定期抽選】全員抽選済みです。")
            return
        erabareta_hito = random.choice(kouho)  
        zumi.append(erabareta_hito.id)
        save_data()
        
        await channel.send(f"【定期抽選】"+"\n"+"今週選ばれたのは... {erabareta_hito.mention} です!")

#Botのメイン処理
@client.event
async def on_ready():
    print(f'{client.user} ログイン完了,準備OK。')
    load_data()
    if not weekly_lottery_task.is_running():
        weekly_lottery_task.start()

#コマンドの処理
@client.event
async def on_message(message):
    global zumi
    if message.author.bot:
        return
    naiyou = message.content.strip()
    server = message.guild
    if not server:
        return
    # 全メンバーのリスト（Bot除く）
    zenin = [m for m in server.members if not m.bot]

    if naiyou.startswith("/help"):
        await message.channel.send("/help - 取説を表示"+"\n"+"/ls - 存在するリストを表示"+
        "\n"+"/cat リスト名 - リストの中を確認"+"\n"+"/add @User1 @User2 - 指定したユーザ(複数可)を未発表リストに戻す"+
        "\n"+"/rm @User1 @User2 - 指定したユーザ(複数可)を発表済リストへ除外する")
        return

    # /lsの処理
    if naiyou.startswith("/ls"):
        await message.channel.send("zumi"+"\n"+"kouho")
        return

    # /catの処理
    if naiyou.startswith('/cat'):
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("確認したいリスト名を引数として入力してください。")
            return
        target_var = args[1]
        if target_var == 'zumi':
            names = []
            for mid in zumi:
                mem = server.get_member(mid)
                if mem:
                    names.append(mem.display_name)
                else:
                    names.append(f"UnknownUser(ID:{mid})")
            if names:
                await message.channel.send(f"抽選済(zumi):\n" + "\n".join(names))
            else:
                await message.channel.send("抽選済は空です。")
        elif target_var == 'kouho':
            kouho = [m.display_name for m in zenin if m.id not in zumi]
            if kouho:
                await message.channel.send(f"未抽選(kouho):\n" + "\n".join(kouho))
            else:
                await message.channel.send("未抽選は空です。")
        else:
            await message.channel.send(f"変数 {target_var} は存在しません。")
        return

    #/addの処理 (未抽選に戻す)
    if naiyou.startswith('/add'):
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("対象を指定してください。\n例: /add @田中 @佐藤, /add /all")
            return

        # /add /all の処理
        if args[1] == '/all':
            zumi = []
            save_data()
            await message.channel.send("メンバー全員を未抽選に戻しました。")
            return

        # メンションと名前テキストの両方を解析して対象リストを作る
        targets = get_targets(message, args, server)
        
        if not targets:
            await message.channel.send("対象のユーザーが見つかりませんでした。")
            return

        processed_names = []
        for taishou in targets:
            if taishou.bot: continue
            if taishou.id in zumi:
                zumi.remove(taishou.id)
                processed_names.append(taishou.display_name)
        
        if processed_names:
            save_data()
            await message.channel.send(f"未抽選に戻しました:\n" + ", ".join(processed_names))
        else:
            await message.channel.send("変更対象がいませんでした（全員既に未抽選かBotです）。")
        return

    #/rmの処理 (抽選済にする)
    if naiyou.startswith('/rm'):
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("対象を指定してください。\n例: /rm @田中 @佐藤, /rm /all")
            return

        # /rm /all の処理
        if args[1] == '/all':
            zumi = [m.id for m in zenin]
            save_data()
            await message.channel.send("全員を抽選済にしました。")
            return

        # メンションと名前テキストの両方を解析して対象リストを作る
        targets = get_targets(message, args, server)

        if not targets:
            await message.channel.send("対象のユーザーが見つかりませんでした。")
            return

        processed_names = []
        for taishou in targets:
            if taishou.bot: continue
            if taishou.id not in zumi:
                zumi.append(taishou.id)
                processed_names.append(taishou.display_name)
        
        if processed_names:
            save_data()
            await message.channel.send(f"抽選済にしました:\n" + ", ".join(processed_names))
        else:
            await message.channel.send("変更対象がいませんでした（全員既に抽選済かBotです）。")
        return

    # 抽選ロジック
    if naiyou.lower() == 'exe':
        kouho = [m for m in zenin if m.id not in zumi]
        if not kouho:
            await message.channel.send("全員抽選済みです。")
            return
        erabareta_hito = random.choice(kouho)
        zumi.append(erabareta_hito.id)
        save_data()
        nokori = len(kouho) - 1
        await message.channel.send(f"選ばれたのは... {erabareta_hito.mention} です!"+"\n"+f"未発表の人は残り{nokori}人!")

client.run(TOKEN)