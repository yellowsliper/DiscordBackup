import asyncio
import discord
import requests
import sqlite3
import datetime
import uuid
import time
from datetime import timedelta
import setting as settings
from setting import 관리자아이디
import base64
import requests
from discord_webhook import DiscordEmbed, DiscordWebhook
from discord_buttons_plugin import ButtonType
from discord.components import Button, ActionRow

intents = discord.Intents.all()
client = discord.Client(intents=intents)

def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

def embed(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x5c6cdf, title=embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=embedtitle, description=description)

def get_expiretime(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간 " + str(round(minutes)) + "분"
    else:
        return False

def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

async def exchange_code(code, redirect_url):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % "https://discord.com/api", data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()

async def refresh_token(refresh_token):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % "https://discord.com/api", data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    print(r.json())
    return False if "error" in r.json() else r.json()

async def add_user(access_token, guild_id, user_id):
    while True:
        jsonData = {"access_token": access_token}
        header = {"Authorization": "Bot " + base64.b64decode(settings.token.encode("ascii")).decode("UTF-8")}
        r = requests.put(
            f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", json=jsonData, headers=header)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    if (r.status_code == 201 or r.status_code == 204):
        return True
    else:
        print(r.json())
        return False

async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get(
        "https://discordapp.com/api/v8/users/@me", headers=header)
    print(res.json())
    if (res.status_code != 200):
        return False
    else:
        return res.json()

def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

async def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True

def eb(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=":no_entry: " + embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x00ff00, title=":white_check_mark: " + embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=":warning: " + embedtitle, description=description)
    if (embedtype == "loading"):
        return discord.Embed(color=0x808080, title=":gear: " + embedtitle, description=description)
    if (embedtype == "primary"):
        return discord.Embed(color=0x82ffc9, title=embedtitle, description=description)

async def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not (await is_guild(id)):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True

owner = [837944214708944896]

@client.event
async def on_ready():
    print(f"Login: {client.user}\nInvite Link: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot")
    while True:
        await client.change_presence(activity=discord.Game(name=str(len(client.guilds)) + "개의 서버 이용"), status=discord.Status.online)
        await asyncio.sleep(3)

@client.event
async def on_message(message):
    if (message.content.startswith(".명령어")):
        if message.author.guild_permissions.administrator:
            await message.reply(embed=discord.Embed(color=0x5c6cdf, title="Backup LS", description=f"**.라이센스 : 라이센스 정보를 조회합니다.\n.웹훅 [웹훅] : 인증이 완료된 유저를 웹훅에 표시합니다.\n.웹훅보기 : 인증 로그가 지정되어 있는 웹훅을 표시합니다.\n.권한 [@권한] : 인증 완료 시 부여할 역할을 지정합니다.\n.복구 [복구키] : 지급된 복구키로 유저 복구를 시작합니다.\n.인증 : 인증 메시지를 보냅니다.\n.커스텀인증 : 인증 메시지를 커스텀합니다.\n.청소 [개수] : 입력한 개수만큼 메시지를 삭제합니다.**"))

    if message.author.id == int(관리자아이디):

        if (message.content.startswith(".생성 ")):
            amount = message.content.split(" ")[1]
            long = message.content.split(" ")[2]
            if (amount.isdigit() and int(amount) >= 1 and int(amount) <= 50):
                con, cur = start_db()
                generated_key = []
                for n in range(int(amount)):
                    key = str(uuid.uuid4())
                    generated_key.append(key)
                    cur.execute("INSERT INTO licenses VALUES(?, ?);", (key, int(long)))
                con.commit()
                con.close()
                generated_key = "\n".join(generated_key)
                await message.channel.send(embed=discord.Embed(title="생성 성공", description="", color=0x5c6cdf))
                await message.channel.send(generated_key)
                webhook = DiscordWebhook(username="Backup LS", avatar_url="https://camo.githubusercontent.com/ae8b7e73273df7fec41117ece8246fd876a43ea443d9e3a6194be883438581c6/68747470733a2f2f692e696d6775722e636f6d2f7934315665434d2e706e67", url="https://canary.discord.com/api/webhooks/1106915804575957102/zEEA-mQbZJ4EADJvShNYGcyg8S-Ceg0yJ0UGIpD1PKgWotiGL9vwfAmya0yc0qts8vEX")
                eb = DiscordEmbed(title='라이센스 생성 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n개수 : {amount}\n기간 : {long} 일\n라이센스 : {generated_key}```', color=0x5c6cdf)
                webhook.add_embed(eb)
                webhook.execute()
            else:
                await message.channel.send(embed=embed("error", "생성 실패", "최대 50개까지 생성 가능합니다."))

        if (message.content.startswith(".서버리스트")):
            guild_list = client.guilds
            for i in guild_list:
                await message.channel.send("서버 ID: {}/ 서버 이름: {}".format(i.id, i.name))

    try:
        if message.author.guild_permissions.administrator:
            if (message.content == (".웹훅보기")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()
                if guild_info[4] == "no":
                    await message.channel.send(embed=embed("error", "Backup LS", "웹훅이 없습니다."))
                    return
                await message.reply(f"{guild_info[4]}")

            if (message.content == (".라이센스")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "유효한 라이센스가 존재하지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()

                con, cur = start_db()
                cur.execute("SELECT * FROM users WHERE guild_id = ?;", (message.guild.id,))
                guild_result = cur.fetchall()
                con.close()

                user_list = []

                for i in range(len(guild_result)):
                    user_list.append(guild_result[i][0])
                
                new_list = []

                for v in user_list:
                    if v not in new_list:
                        new_list.append(v)

                await message.channel.send(embed=embed("success", "Backup LS", f"만료일 : `{guild_info[3]}`\n남은 기간 : `{get_expiretime(guild_info[3])}`\n 인증 유저 수 : `{len(new_list)}`명"))
    except:
        pass

    try:
        if (message.guild != None or message.author.id in owner or message.author.guild_permissions.administrator):
            if (message.content.startswith(".등록 ")):
                license_number = message.content.split(" ")[1]
                con, cur = start_db()
                cur.execute("SELECT * FROM licenses WHERE key == ?;", (license_number,))
                key_info = cur.fetchone()
                if (key_info == None):
                    con.close()
                    await message.channel.send(embed=embed("error", "Backup LS", "존재하지 않거나 이미 사용된 라이센스입니다."))
                    return
                cur.execute("DELETE FROM licenses WHERE key == ?;", (license_number,))
                con.commit()
                con.close()
                key_length = key_info[1]

                if (await is_guild(message.guild.id)):
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                    guild_info = cur.fetchone()
                    expire_date = guild_info[3]
                    if (is_expired(expire_date)):
                        new_expiredate = make_expiretime(key_length)
                    else:
                        new_expiredate = add_time(expire_date, key_length)
                    cur.execute("UPDATE guilds SET expiredate = ? WHERE id == ?;", (new_expiredate, message.guild.id))
                    con.commit()
                    con.close()
                    await message.channel.send(embed=embed("success", "Backup LS", f"{key_length} 일 라이센스가 성공적으로 연장되었습니다."))
                    webhook = DiscordWebhook(username="Backup LS", avatar_url="https://camo.githubusercontent.com/ae8b7e73273df7fec41117ece8246fd876a43ea443d9e3a6194be883438581c6/68747470733a2f2f692e696d6775722e636f6d2f7934315665434d2e706e67", url=" https://discord.com/api/oauth2/authorize?client_id=993748105205923851&redirect_uri=http://dayun.pythonanywhere.com/%2Fcallback&response_type=code&scope=identify%20guilds.join&state=1106915023399432252")
                    eb = DiscordEmbed(title='서버 연장 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n기간 : {key_length} 일\n라이센스 : {message.content.split(" ")[1]}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()
                else:
                    con, cur = start_db()
                    new_expiredate = make_expiretime(key_length)
                    recover_key = str(uuid.uuid4())[:8].upper()
                    cur.execute("INSERT INTO guilds VALUES(?, ?, ?, ?, ?, ?);", (message.guild.id, 0, recover_key, new_expiredate, "no", "파랑"))
                    con.commit()
                    con.close()
                    # await message.channel.send(f"{message.author.mention}님 디엠을 확인해주세요.")
                    await message.channel.send(embed=embed("success", f"{message.guild.name}", f"복구키 : **`{recover_key}`**\n복구키는 복구를 할 때 쓰이니 꼭 기억해주세요."))
                    webhook = DiscordWebhook(username="Backup LS", avatar_url="https://camo.githubusercontent.com/ae8b7e73273df7fec41117ece8246fd876a43ea443d9e3a6194be883438581c6/68747470733a2f2f692e696d6775722e636f6d2f7934315665434d2e706e67", url=" https://discord.com/api/oauth2/authorize?client_id=993748105205923851&redirect_uri=http://dayun.pythonanywhere.com/%2Fcallback&response_type=code&scope=identify%20guilds.join&state=1106915023399432252")
                    eb = DiscordEmbed(title='서버 등록 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n기간 : {key_length} 일\n라이센스 : {message.content.split(" ")[1]}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()
    except AttributeError:
        pass

    try:
        if message.author.guild_permissions.administrator:
            if (message.content == ".인증"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                await message.delete()
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                server_info = cur.fetchone()
                con.close()
                if server_info[5] == "파랑":
                    color = 0x5c6cdf
                if server_info[5] == "빨강":
                    color = 0xff4848
                if server_info[5] == "초록":
                    color = 0x00ff27
                if server_info[5] == "검정":
                    color = 0x010101
                if server_info[5] == "회색":
                    color = 0xd1d1d1
                await message.channel.send(embed=discord.Embed(color=color, title=f"{message.guild.name}", description=f"Please authorize your account [here](https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20guilds.join&state={message.guild.id}) to see other channels.\n다른 채널을 보려면 [여기](https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20guilds.join&state={message.guild.id}) 를 눌러 계정을 인증해주세요."))

            if (message.content == ".커스텀인증"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                await message.delete()
                custom = await message.channel.send(embed=discord.Embed(title='Backup LS', description='설정할 인증 메시지를 입력해주세요.',color=0x5c6cdf))
                def check(msg):
                    return (msg.author.id == message.author.id)
                try:
                    msg = await client.wait_for("message", timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.channel.send(embed=discord.Embed(title="시간 초과",color=0x5c6cdf))
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                server_info = cur.fetchone()
                con.close()
                if server_info[5] == "파랑":
                    color = 0x5c6cdf
                if server_info[5] == "빨강":
                    color = 0xff4848
                if server_info[5] == "초록":
                    color = 0x00ff27
                if server_info[5] == "검정":
                    color = 0x010101
                if server_info[5] == "회색":
                    color = 0xd1d1d1
                await custom.delete()
                await msg.delete()
                await message.channel.send(embed=discord.Embed(color=color, title=f"{message.guild.name}", description=f"{msg.content}"),
                components=[
                    ActionRow(
                        Button(style=ButtonType().Link, label="인증하러 가기",
                            url=f"https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}/callback&response_type=code&scope=identify%20guilds.join&state={message.guild.id}")
                    )
                ])

            if message.content.startswith(".청소"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                amount = message.content[4:]
                await message.channel.purge(limit=1)
                await message.channel.purge(limit=int(amount))
                await message.channel.send(embed=discord.Embed(title="Backup LS", description="{}개의 메시지 청소가 완료되었습니다.".format(amount), color=0x5c6cdf))

            if message.content.startswith(".색깔"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                await message.channel.send(embed=discord.Embed(title='Backup LS', description='원하시는 색깔을 입력해주세요. ( **파랑**, **빨강**, **초록**, **회색**, **검정** )',color=0x5c6cdf))
                def check(msg):
                    return (msg.author.id == message.author.id)
                try:
                    msg = await client.wait_for("message", timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.channel.send(embed=discord.Embed(title="시간 초과",color=0x5c6cdf))
                else:
                    if msg.content == "파랑" or msg.content == "빨강" or msg.content == "초록" or msg.content == "회색" or msg.content == "검정":
                        try:
                            color = msg.content
                            con, cur = start_db()
                            cur.execute("UPDATE guilds SET color == ? WHERE id = ?;",(color, message.guild.id))
                            con.commit()
                            con.close()
                        except Exception:
                            await message.channel.send(embed=discord.Embed(title='Backup LS', description='알 수 없는 오류입니다.', color=0xff0000))
                        else:
                            await message.channel.send(embed=discord.Embed(title="Backup LS", description=f"성공적으로 버튼 및 임베드 색깔이 변경되었습니다.", color=0x5c6cdf))
                    else:
                        await message.channel.send(embed=discord.Embed(title='Backup LS', description='색깔은 **파랑**, **빨강**, **초록**, **회색**, **검정**만 지정 가능합니다.', color=0xff0000))

            if message.content.startswith(".웹훅 "):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
                    return
                webhook = message.content.split(" ")[1]
                if webhook == "no":
                    await message.reply("no는 웹훅이 아닙니다.")
                    return

                con, cur = start_db()
                cur.execute("UPDATE guilds SET verify_webhook == ? WHERE id = ?;", (str(
                    webhook), message.guild.id))
                con.commit()
                con.close()
                await message.reply(embed=embed("success", "Backup LS", f"웹훅 설정이 완료되었습니다."))

            if (message.content.startswith(".권한 <@&") and message.content[-1] == ">"):
                if (await is_guild_valid(message.guild.id)):
                    mentioned_role_id = message.content.split(
                        " ")[1].split("<@&")[1].split(">")[0]
                    if not (mentioned_role_id.isdigit()):
                        await message.channel.send(embed=embed("error", "Backup LS", "존재하지 않는 역할입니다."))
                        return
                    mentioned_role_id = int(mentioned_role_id)
                    role_info = message.guild.get_role(mentioned_role_id)
                    if (role_info == None):
                        await message.channel.send(embed=embed("error", "Backup LS", "존재하지 않는 역할입니다."))
                        return
                    con, cur = start_db()
                    cur.execute("UPDATE guilds SET role_id = ? WHERE id == ?;", (mentioned_role_id, message.guild.id))
                    con.commit()
                    con.close()
                    await message.channel.send(embed=embed("success", "Backup LS", f"인증을 완료한 유저에게 <@&{mentioned_role_id}> 역할이 지급됩니다."))
                else:
                    await message.channel.send(embed=embed("error", "Backup LS", "서버가 등록되어 있지 않습니다."))
    except AttributeError:
        pass
    
    try:
        if message.author.guild_permissions.administrator:
            if (message.content.startswith(".복구 ")):
                recover_key = message.content.split(" ")[1]
                if (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Backup LS", "라이센스 등록 전에 복구를 진행하셔야 합니다."))
                else:
                    await message.delete()
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE token == ?;", (recover_key,))
                    token_result = cur.fetchone()
                    con.close()
                    if (token_result == None):
                        await message.channel.send(embed=embed("error", "Backup LS", "존재하지 않는 복구키입니다."))
                        return
                    if not (await is_guild_valid(token_result[0])):
                        await message.channel.send(embed=embed("error", "Backup LS", "만료된 복구키입니다."))
                        return
                    try:
                        server_info = await client.fetch_guild(token_result[0])
                    except:
                        server_info = None
                        pass
                    if not (await message.guild.fetch_member(client.user.id)).guild_permissions.administrator:
                        await message.channel.send(embed=embed("error", "Backup LS", "봇이 관리자 권한을 가지고 있어야 합니다."))
                        return
                        
                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
                    users = cur.fetchall()
                    con.close()
                    users = list(set(users))

                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE token = ?;", (recover_key,))
                    server = cur.fetchone()[0]
                    con.close()

                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id = ?;", (server,))
                    guild_result = cur.fetchall()
                    con.close()

                    user_list = []

                    for i in range(len(guild_result)):
                        user_list.append(guild_result[i][0])
                
                    new_list = []

                    for v in user_list:
                        if v not in new_list:
                            new_list.append(v)

                    await message.channel.send(embed=embed("success", "Backup LS", f"유저를 복구 중입니다. 최대 1시간이 소요될 수 있습니다. ( 예상 복구 인원 : {len(new_list)} )"))
                    
                    webhook = DiscordWebhook(username="Backup LS", avatar_url="https://camo.githubusercontent.com/ae8b7e73273df7fec41117ece8246fd876a43ea443d9e3a6194be883438581c6/68747470733a2f2f692e696d6775722e636f6d2f7934315665434d2e706e67", url=" https://discord.com/api/oauth2/authorize?client_id=993748105205923851&redirect_uri=http://dayun.pythonanywhere.com/%2Fcallback&response_type=code&scope=identify%20guilds.join&state=1106915023399432252")
                    eb = DiscordEmbed(title='복구 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n복구키 : {recover_key}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()

                    for user in users:
                        try:
                            refresh_token1 = user[1]
                            user_id = user[0]
                            new_token = await refresh_token(refresh_token1)
                            if (new_token != False):
                                new_refresh = new_token["refresh_token"]
                                new_token = new_token["access_token"]
                                await add_user(new_token, message.guild.id, user_id)
                                print(new_token)
                                con,cur = start_db()
                                cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                                con.commit()
                                con.close()
                                time.sleep(2)
                        except:
                            time.sleep(2)
                            pass
                        
                    con,cur = start_db()
                    cur.execute("UPDATE users SET guild_id = ? WHERE guild_id == ?;", (message.guild.id, token_result[0]))
                    con.commit()
                    cur.execute("UPDATE guilds SET id = ? WHERE id == ?;", (message.guild.id, token_result[0]))
                    con.commit()
                    con.close()

                    await message.channel.send(embed=embed("success", "Backup LS", "유저 복구가 완료되었습니다. 기존 라이센스와 복구키는 모두 이동됩니다."))
    except AttributeError:
        pass

def botrun(token):
    client.run(token)
