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
CHANNEL_ID = CHID
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
        # ディレクトリが存在しない場合は作成する処理を追加しておくと安全です
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
#定期実行タスク
@tasks.loop(time=datetime.time(hour=10, minute=45, tzinfo=JST))
async def weekly_lottery_task():
    #今日の曜日を日本時間でチェック
    now_jst = datetime.datetime.now(JST)
    if now_jst.weekday() == 4:
        #指定されたチャンネルを取得
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
    #定期実行タスクを開始
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
        "\n"+"/cat リスト名 - リストの中を確認"+"\n"+"/add ユーザ名 - これから発表するユーザを追加"+
        "\n"+"/rm ユーザ名 - 指定したユーザを発表済リストへ除外する")
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
                await message.channel.send(f"抽選済:\n" + "\n".join(names))
            else:
                await message.channel.send("抽選済は空です。")
        elif target_var == 'kouho':
            kouho = [m.display_name for m in zenin if m.id not in zumi]
            
            if kouho:
                await message.channel.send(f"未抽選:\n" + "\n".join(kouho))
            else:
                await message.channel.send("未抽選は空です。")
        else:
            await message.channel.send(f"変数 {target_var} は存在しません。")
        return
    #/addの処理
    if naiyou.startswith('/add'):
        args = naiyou.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send("対象を指定してください。\n例: /add @田中, /add /all")
            return
        target_str = args[1]
        if target_str == '/all':
            zumi = []
            save_data()
            await message.channel.send("メンバー全員を未抽選に戻しました。")
            return
        taishou = None
        if message.mentions:
            taishou = message.mentions[0]
        else:
            taishou = discord.utils.find(lambda m: m.display_name == target_str or m.name == target_str, server.members)

        if taishou:
            if taishou.id in zumi:
                zumi.remove(taishou.id)
                save_data()
                await message.channel.send(f"{taishou.display_name} さんを未抽選に戻しました。")
            else:
                await message.channel.send(f"{taishou.display_name} さんは最初から未抽選です。")
        else:
            await message.channel.send(f"「{target_str}」さんが見つかりません。")
        return
    #/rmの処理
    if naiyou.startswith('/rm'):
        args = naiyou.split(maxsplit=1)
        if len(args) < 2:
            await message.channel.send("対象を指定してください。")
            return
        target_str = args[1]
        #/rm /all の処理
        if target_str == '/all':
            zumi = [m.id for m in zenin]
            save_data()
            await message.channel.send("全員を抽選済にしました。")
            return
        taishou = None
        if message.mentions:
            taishou = message.mentions[0]
        else:
            taishou = discord.utils.find(lambda m: m.display_name == target_str or m.name == target_str, server.members)
        if taishou:
            if taishou.id not in zumi:
                zumi.append(taishou.id)
                save_data()
                await message.channel.send(f"{taishou.display_name} さんを抽選済にしました。")
            else:
                await message.channel.send(f"{taishou.display_name} さんは既に抽選済です。")
        else:
            await message.channel.send(f"「{target_str}」さんが見つかりません。")
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


