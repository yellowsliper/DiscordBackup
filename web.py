import flask
from datetime import timedelta
import setting as settings
import asyncio
import requests
import sqlite3
import datetime
from fastapi import FastAPI
import base64
import w
from flask import request
import discord
import bot
import threading

client = discord.Client(intents=discord.Intents.all())
app = flask.Flask(__name__)
apps = FastAPI()



def get_kr_time():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

def getip():
    return request.headers.get("CF-Connecting-IP", request.remote_addr)

def get_agent():
    return request.user_agent.string

def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

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
    ExpireTime_STR = (ServerTime + timedelta(days=days)
                      ).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)
                      ).strftime('%Y-%m-%d %H:%M')
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
        r = requests.post(
            "https://discord.com/api/oauth2/token", data=data, headers=headers)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()

async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get(
        "https://discordapp.com/api/v9/users/@me", headers=header)
    if (res.status_code != 200):
        return False
    else:
        return res.json()

def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True

def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not is_guild(id):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True

@app.route("/")
def main():
    return "Backup bot is running"

@app.route("/callback", methods=["GET"])
async def callback():
    state = request.args.get('state')
    code = request.args.get('code')
    if not (str(state).isdigit()):
        print('1')
        return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
    elif not is_guild_valid(state):
        print('2')
        return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
    exchange_res = await exchange_code(code, f"{settings.base_url}/callback")
    if (exchange_res == False):
        print('3')
        return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
    user_info = await get_user_profile("Bearer " + exchange_res["access_token"])
    if (user_info == False):
        print('5')
        return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
    try:
        asyncio.create_task(client.start(base64.b64decode(settings.token.encode("ascii")).decode("UTF-8")))
    except Exception as e:
        print(e)
    else:
        await asyncio.sleep(1)
        try:
            guild = await client.fetch_guild(int(state))
        except Exception as e:
            print('6')
            return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
        try:
            user = await guild.fetch_member(int(user_info["id"]))
        except Exception as e:
            print(e)
            print('6')
            return flask.render_template("error.html", title="인증 실패", dese="터졌거나 존재하지 않는 인증 링크입니다.")
        if user == None:
            print('7')
            return flask.render_template("error.html", title="인증 실패", dese="서버에 입장해 있지 않는 유저입니다.")


        con, cur = start_db()
        cur.execute("INSERT INTO users VALUES(?, ?, ?);", (str(
            user_info["id"]), exchange_res["refresh_token"], int(state)))
        con.commit()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        roleid = cur.fetchone()[1]
        con.close()

        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        webhook = str(cur.fetchone()[4])
        con.commit()
        con.close()
        role = guild.get_role(roleid)
        if role == None:
            return flask.render_template("error.html", title="인증 실패", dese=f"**{user.name}#{user.discriminator}** 님, `{guild.name}` 서버는 아직 지급 역할 세팅이 되지 않았습니다.")
        try:
            await user.add_roles(role)
        except Exception as e:
            print(e)
            return flask.render_template("error.html", title="인증 실패", dese=f"**{user.name}#{user.discriminator}** 님, `{guild.name}` 서버에서 역할 지급 중 오류가 발생했습니다.")
        try:
            await user.send(embed=discord.Embed(title=f"{guild.name}", description=f"<@{user.id}>님, {guild.name} 인증이 완료되었습니다.\n\n지급 시간 : {get_kr_time()}", color=0x5c6cdf))
        except:
            pass
        try:
            if not webhook == "no":
                w.send(webhook, f"{user.name}#{user.discriminator} ({user.id})", f"<@{user.id}>님이 인증을 완료하였습니다.\n```유저 정보 : {user.name}#{user.discriminator}\n인증 서버 : {guild.name}\n역할 정보 : {role.name}({roleid})```", f"")
        except:
            pass
        else:
            return flask.render_template("ok.html", title="인증 성공", nickname=f"닉네임 : {user.name}#{user.discriminator}", server=f"서버 이름 : {guild.name}", role=f"역할 정보 : {role.name}")


def webrun():
    app.run(host='0.0.0.0', port=6456)

def flask_thread(func):
    thread = threading.Thread(target=func)
    thread.start()

flask_thread(func=webrun)
bot.botrun(base64.b64decode(settings.token.encode("ascii")).decode("UTF-8"))