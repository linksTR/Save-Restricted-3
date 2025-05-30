# ---------------------------------------------------
# Dosya Adi: func.py
# Aciklama: Telegram kanallarindan veya gruplarindan dosya indirmek ve
# onlari tekrar Telegram'a yuklemek icin bir Pyrogram botu.
# Yazar: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Olusturulma Tarihi: 2025-01-11
# Son Degisiklik: 2025-01-11
# Surum: 2.0.6
# Lisans: MIT Lisansi
# ---------------------------------------------------

import math
import time, re
from pyrogram import enums
from config import CHANNEL_ID, OWNER_ID, MONGO_DB
from devgagan.core.mongo.plans_db import premium_users
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import cv2
from pyrogram.errors import FloodWait, InviteHashInvalid, InviteHashExpired, UserAlreadyParticipant, UserNotParticipant
from datetime import datetime as dt
import asyncio, subprocess, re, os, time

async def check_bot_mode():
    """Botun ucretsiz modda olup olmadigini veritabanindan kontrol eder"""
    if MONGO_DB:
        from devgagan.core.mongo.plans_db import db
        mode_data = await db.bot_mode.find_one({"_id": "mode"})
        return mode_data.get("free_mode", False) if mode_data else False
    return False

async def chk_user(message, user_id):
    """Kullanicinin erisim haklarini moda gore kontrol eder"""
    free_mode = await check_bot_mode()
    if free_mode:
        return 0 # Ucretsiz mod - herkese izin ver
    
    user = await premium_users()
    if user_id in user or user_id in OWNER_ID:
        return 0
    return 1

async def gen_link(app, chat_id):
    """Bir sohbet icin davet linki olusturur"""
    link = await app.export_chat_invite_link(chat_id)
    return link

async def subscribe(app, message):
    """Kanal abonelik gereksinimini kontrol eder"""
    free_mode = await check_bot_mode()
    if free_mode:
        return 0 # Ucretsiz modda kanal katilim kontrolunu atla
        
    update_channel = CHANNEL_ID
    url = await gen_link(app, update_channel)
    if update_channel:
        try:
            user = await app.get_chat_member(update_channel, message.from_user.id)
            if user.status == "kicked":
                await message.reply_text("Yaslandiniz. Iletisim -- @denujke")
                return 1
        except UserNotParticipant:
            caption = "Botu kullanmak icin kanalimiza katilin"
            await message.reply_photo(
                photo="https://www.facebook.com/photo.php?fbid=1399096156913108&id=212657025557033&set=a.254003098089092", # Bu URL'nin erisilebilir oldugundan emin olun.
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Simdi Katil...", url=f"{url}")]
                ])
            )
            return 1
        except Exception:
            await message.reply_text("Bir seyler ters gitti. Bize ulasin @denujke")
            return 1

async def get_seconds(time_string):
    """Zaman dizesini saniyeye donusturur"""
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].lstrip()
        if value:
            value = int(value)
        return value, unit

    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    return 0

PROGRESS_BAR = """
| **__Tamamlandi:__** {1}/{2}
| **__Bayt:__** {0}%
| **__Hiz:__** {3}/s
| **__Tahmini Sure:__** {4}
╰─────────────────────╯
"""

async def progress_bar(current, total, ud_type, message, start):
    """Islemler icin ilerleme cubugunu gosterir"""
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["♦" for i in range(math.floor(percentage / 10))]),
            ''.join(["◇" for i in range(10 - math.floor(percentage / 10))]))

        tmp = progress + PROGRESS_BAR.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(text="{}\n| {}".format(ud_type, tmp))
        except:
            pass

def humanbytes(size):
    """Baytlari insan tarafindan okunabilir formata donusturur"""
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def TimeFormatter(milliseconds: int) -> str:
    """Milisaniyeleri okunabilir zamana bicimlendirir"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "g, ") if days else "") + \
        ((str(hours) + "s, ") if hours else "") + \
        ((str(minutes) + "d, ") if minutes else "") + \
        ((str(seconds) + "sn, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def convert(seconds):
    """Saniyeleri SS:DD:SS formatina donusturur"""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def userbot_join(userbot, invite_link):
    """Kullanici botu ile kanala katilir"""
    try:
        await userbot.join_chat(invite_link)
        return "Kanala basariyla katildi"
    except UserAlreadyParticipant:
        return "Kullanici zaten katilimci."
    except (InviteHashInvalid, InviteHashExpired):
        return "Katilamadi. Belki linkiniz suresi dolmus veya gecersiz."
    except FloodWait:
        return "Cok fazla istek var, daha sonra tekrar deneyin."
    except Exception as e:
        print(e)
        return "Katilamadi, manuel olarak katilmayi deneyin."

def get_link(string):
    """Dizeden URL cikarir"""
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    try:
        link = [x[0] for x in url][0]
        return link if link else False
    except Exception:
        return False

def video_metadata(file):
    """OpenCV kullanarak video meta verilerini alir"""
    default_values = {'width': 1, 'height': 1, 'duration': 1}
    try:
        vcap = cv2.VideoCapture(file)
        if not vcap.isOpened():
            return default_values

        width = round(vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = round(vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = vcap.get(cv2.CAP_PROP_FPS)
        frame_count = vcap.get(cv2.CAP_PROP_FRAME_COUNT)

        if fps <= 0:
            return default_values

        duration = round(frame_count / fps)
        if duration <= 0:
            return default_values

        vcap.release()
        return {'width': width, 'height': height, 'duration': duration}
    except Exception as e:
        print(f"video_metadata'da hata: {e}")
        return default_values

def hhmmss(seconds):
    """Saniyeleri HH:MM:SS formatina donusturur"""
    return time.strftime('%H:%M:%S', time.gmtime(seconds))

async def screenshot(video, duration, sender):
    """Videodan ekran goruntusu alir"""
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    time_stamp = hhmmss(int(duration)/2)
    out = dt.now().isoformat("_", "seconds") + ".jpg"
    cmd = ["ffmpeg",
           "-ss", f"{time_stamp}",
           "-i", f"{video}",
           "-frames:v", "1",
           f"{out}", "-y"]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if os.path.isfile(out):
        return out
    return None

last_update_time = time.time()
async def progress_callback(current, total, progress_message):
    """Yuklemeler icin ilerleme geri cagirisi"""
    percent = (current / total) * 100
    global last_update_time
    current_time = time.time()

    if current_time - last_update_time >= 10 or percent % 10 == 0:
        completed_blocks = int(percent // 10)
        remaining_blocks = 10 - completed_blocks
        progress_bar = "♦" * completed_blocks + "◇" * remaining_blocks
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        await progress_message.edit(
            f"╭──────────────────╮\n"
            f"│           **__Yukleniyor...__** \n"
            f"├──────────\n"
            f"│ {progress_bar}\n\n"
            f"│ **__Ilerleme:__** {percent:.2f}%\n"
            f"│ **__Yuklendi:__** {current_mb:.2f} MB / {total_mb:.2f} MB\n"
            f"╰──────────────────╯\n\n"
            f"**__Lutfen bekleyin__**"
        )
        last_update_time = current_time

async def prog_bar(current, total, ud_type, message, start):
    """Alternatif ilerleme cubugu uygulamasi"""
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["♦" for i in range(math.floor(percentage / 10))]),
            ''.join(["◇" for i in range(10 - math.floor(percentage / 10))]))

        tmp = progress + PROGRESS_BAR.format(
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit_text(text="{}\n| {}".format(ud_type, tmp))
        except:
            pass

