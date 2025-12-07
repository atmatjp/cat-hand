import discord
import random
import os
from dotenv import load_dotenv
from discord.ext import tasks
import datetime

#.envの読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
CHID = os.getenv("CHANNEL_ID")
CHANNEL_ID = int(CHID) if CHID and CHID.isdigit() else None
#時間設定の読み込み(デフォルト値付き)
SCHEDULE_HOUR = int(os.getenv('SCHEDULE_HOUR'))
SCHEDULE_MINUTE = int(os.getenv('SCHEDULE_MINUTE'))
SCHEDULE_WEEKDAY = int(os.getenv('SCHEDULE_WEEKDAY'))

#デフォルトの権限設定を取得
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
#botクライアントを作成
client = discord.Client(intents=intents)
DATA_FILE = "./data/zumi.txt"
#抽選済みの人のIDを入れるリスト
zumi = []
#日本標準時
JST = datetime.timezone(datetime.timedelta(hours=9))
def save_data():
    try:
        #ファイルを入れるフォルダ(./data)がない場合、自動で作る
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        #ファイルを書き込みモード'w'
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            #抽選済リストに入っているIDを一つずつ取り出す
            for user_id in zumi:
                #IDを文字列にして書き込み、改行(\n)を入れる
                f.write(str(user_id) + '\n')
        print("データを外部ファイルに格納しました。")
    except Exception as e:
        #もし保存に失敗したらエラー内容を表示する
        print(f"格納に失敗: {e}")
def load_data():
    global zumi
    if os.path.exists(DATA_FILE):
        try:
            #ファイルを読み込みモードで開く
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                zumi = [int(line.strip()) for line in f.readlines()]
            print(f"変数格納ファイルを読み込みました。現在の除外人数: {len(zumi)}人")
        except Exception as e:
            print(f"外部にある変数格納ファイルの読み込みに失敗しました: {e}")
def get_targets(message, args, server):
    #見つかったメンバーを入れるリスト
    targets = []
    #message.mentionsにはメンションされたメンバー情報が自動で入っている
    if message.mentions:
        targets.extend(message.mentions)
    name_list = args[1:]
    for name_str in name_list:
        if name_str.startswith('<@') and name_str.endswith('>'):
            continue
        #discord.utils.findは条件に合う最初の1人を見つける機能
        found_member = discord.utils.find(lambda m: m.display_name == name_str or m.name == name_str, server.members)
        #もし見つかって、かつ、まだリストに入っていない人なら追加する
        if found_member and found_member not in targets:
            targets.append(found_member)      
    #見つかったメンバー全員のリストを返す
    return targets
#定期実行
@tasks.loop(time=datetime.time(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, tzinfo=JST))
async def weekly_lottery_task():
    #現在の日本時間を取得
    now_jst = datetime.datetime.now(JST)
    if now_jst.weekday() == SCHEDULE_WEEKDAY:
        #チャンネルID設定がない場合は中断
        if not CHANNEL_ID:
            print("チャンネルIDが設定されていません。")
            return
        #Botが知っているチャンネル情報からIDを使ってチャンネルを取得
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print(f"エラー: チャンネルID {CHANNEL_ID} が見つかりません。")
            return
        server = channel.guild
        #サーバーにいるBot以外の全メンバーを取得
        zenin = [m for m in server.members if not m.bot]
        #全メンバーの中から「まだ抽選済リストに入っていない人」だけを選び出す
        kouho = [m for m in zenin if m.id not in zumi]
        #もし候補者がいなかったら終了
        if not kouho:
            await channel.send("【定期抽選】全員抽選済みです。")
            return
        #候補者の中からランダムに一人選ぶ
        erabareta_hito = random.choice(kouho)
        #選ばれた人のIDを抽選済リストに追加
        zumi.append(erabareta_hito.id)
        #ファイルを保存
        save_data()
        #選ばれた人物をメンション付きで発表
        await channel.send(f"【定期抽選】"+"\n"+"今週選ばれたのは..."+f"{erabareta_hito.mention} です!"+"\n"+"よろしくお願いします!")
#Botが起動して準備完了した時に動く処理
@client.event
async def on_ready():
    print(f'{client.user} ログイン完了,準備OK。')
    #起動時に一度だけ保存データを読み込む
    load_data()
    #定期タスクがまだ動いていなければスタート
    if not weekly_lottery_task.is_running():
        weekly_lottery_task.start()
#誰かがメッセージを送信した時に動く処理
@client.event
async def on_message(message):
    global zumi
    #Bot自身の発言は無視する
    if message.author.bot:
        return
    naiyou = message.content.strip()
    server = message.guild
    if not server:
        return
    #サーバーにいるBot以外の全メンバーを取得しておく
    zenin = [m for m in server.members if not m.bot]
    #/help 名前の通り
    if naiyou.startswith("/help"):
        await message.channel.send("/help - 取説を表示"+"\n"+"/ls - 存在するリストを表示"+
        "\n"+"/cat リスト名 - リストの中を確認"+"\n"+"/add @User1 @User2 - 指定したユーザを未抽選リストに戻す"+
        "\n"+"/rm @User1 @User2 - 指定したユーザを抽選済リストへ除外する")
        return
    #/ls どんなリストが存在しているのか確認するためのコマンド(正直いらない)
    if naiyou.startswith("/ls"):
        await message.channel.send("zumi"+"\n"+"kouho")
        return
    #/cat リストの中身を確認するコマンド
    if naiyou.startswith('/cat'):
        #スペースで区切って単語のリストにする
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("確認したいリスト名を引数として入力してください。")
            return
        target_var = args[1]
        #抽選済リストを表示する場合
        if target_var == 'zumi':
            names = []
            #IDのリストからメンバー情報を探して名前を取得するループ
            for mid in zumi:
                mem = server.get_member(mid)
                if mem:
                    names.append(mem.display_name)
                else:
                    #退会した人などは名前が取れないらしいのでIDを表示
                    names.append(f"UnknownUser(ID:{mid})")
            if names:
                await message.channel.send(f"抽選済(zumi):\n" + "\n".join(names))
            else:
                await message.channel.send("抽選済は空です。")
        #未抽選リストを表示する場合
        elif target_var == 'kouho':
            #全メンバーから抽選済に含まれていない人物の名前リストを作成する
            kouho = [m.display_name for m in zenin if m.id not in zumi]
            if kouho:
                await message.channel.send(f"未抽選(kouho):\n" + "\n".join(kouho))
            else:
                await message.channel.send("未抽選は空です。")
        else:
            await message.channel.send(f"変数 {target_var} は存在しません。")
        return
    #/add 指定した人物を未抽選リストに格納 複数人選択可
    if naiyou.startswith('/add'):
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("対象を指定してください。\n例: /add @田中 @佐藤, /add /all")
            return
        #/allが指定されたら全員リセット
        if args[1] == '/all':
            zumi = []
            save_data()
            await message.channel.send("メンバー全員を未抽選に戻しました。")
            return
        targets = get_targets(message, args, server)
        
        if not targets:
            await message.channel.send("対象のユーザーが見つかりませんでした。")
            return

        processed_names = []
        for taishou in targets:
            if taishou.bot: continue
            #もし抽選済リストに入っている人ならリストから除外(未抽選に戻るだけ)
            if taishou.id in zumi:
                zumi.remove(taishou.id)
                processed_names.append(taishou.display_name)
        if processed_names:
            save_data()
            await message.channel.send(f"未抽選に戻しました:\n" + ", ".join(processed_names))
        else:
            await message.channel.send("変更対象がいませんでした（全員既に未抽選かBotです）。")
        return
    #/rm 指定した人物を抽選済リストに格納
    if naiyou.startswith('/rm'):
        args = naiyou.split()
        if len(args) < 2:
            await message.channel.send("対象を指定してください。\n例: /rm @田中 @佐藤, /rm /all")
            return
        #/allが指定されたら全員を抽選済みにする処理
        if args[1] == '/all':
            zumi = [m.id for m in zenin]
            save_data()
            await message.channel.send("全員を抽選済にしました。")
            return
        targets = get_targets(message, args, server)
        if not targets:
            await message.channel.send("対象のユーザーが見つかりませんでした。")
            return
        processed_names = []
        for taishou in targets:
            if taishou.bot: continue
            #まだ抽選済リストに入っていない人なら追加
            if taishou.id not in zumi:
                zumi.append(taishou.id)
                processed_names.append(taishou.display_name)
        if processed_names:
            save_data()
            await message.channel.send(f"抽選済にしました:\n" + ", ".join(processed_names))
        else:
            await message.channel.send("変更対象がいませんでした（全員既に抽選済かBotです）。")
        return
    #手動で抽選する時の処理
    if naiyou.lower() == 'pick': # <-- 'exe' から 'pick' に変更
        #Bot以外の全メンバーから、抽選済に含まれていない人を選ぶ
        kouho = [m for m in zenin if m.id not in zumi]
        #候補がいなければ終了
        if not kouho:
            await message.channel.send("全員抽選済みです。")
            return
        erabareta_hito = random.choice(kouho)
        #選ばれた人を抽選済リストに追加
        zumi.append(erabareta_hito.id)
        #保存する
        save_data()
        #残りの人数を計算
        nokori = len(kouho) - 1
        await message.channel.send(f"選ばれたのは... {erabareta_hito.mention} です!"+"\n"+f"未発表の人は残り{nokori}人!")
#Botを起動
client.run(TOKEN)