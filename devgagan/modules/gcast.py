# ---------------------------------------------------
# Dosya Adı: gcast.py
# Açıklama: Telegram kanallarından veya gruplarından dosya indirmek ve
# onları tekrar Telegram'a yüklemek için bir Pyrogram botu.
# Yazar: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Oluşturulma Tarihi: 2025-01-11
# Son Değişiklik: 2025-01-11
# Sürüm: 2.0.5
# Lisans: MIT Lisansı
# ---------------------------------------------------

import asyncio
from pyrogram import filters
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid
)
import traceback # traceback modülü hata izlemeyi yakalamak için eklendi
from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users

async def send_msg(user_id, message):
    try:
        x = await message.copy(chat_id=user_id)
        try:
            await x.pin()
        except Exception:
            await x.pin(both_sides=True)
        return 200, "Mesaj başarıyla gönderildi." # Başarı durumunu döndür
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await send_msg(user_id, message) # Kendini tekrar çağır
    except InputUserDeactivated:
        return 400, f"{user_id} : devre dışı bırakıldı\n"
    except UserIsBlocked:
        return 400, f"{user_id} : botu engelledi\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : kullanıcı ID'si geçersiz\n"
    except Exception:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    if not message.reply_to_message:
        await message.reply_text("Yayınlamak için bir mesaja yanıt verin.")
        return
    exmsg = await message.reply_text("Yayın başlatılıyor!")
    all_users = (await get_users()) or [] # Veritabanından tüm kullanıcı ID'lerini al
    done_users = 0
    failed_users = 0

    for user_id in all_users: # all_users doğrudan kullanıcı ID'lerini içeriyorsa
        status_code, _ = await send_msg(user_id, message.reply_to_message)
        if status_code == 200:
            done_users += 1
        else:
            failed_users += 1
        await asyncio.sleep(0.1) # Flood sınırı için küçük bir gecikme

    if failed_users == 0:
        await exmsg.edit_text(
            f"**Başarıyla yayınlandı ✅**\n\n**Mesaj gönderilen kullanıcı sayısı:** `{done_users}`"
        )
    else:
        await exmsg.edit_text(
            f"**Başarıyla yayınlandı ✅**\n\n**Mesaj gönderilen kullanıcı sayısı:** `{done_users}`\n\n**Not:-** `Bazı sorunlar nedeniyle` `{failed_users}` **kullanıcıya yayın yapılamadı**"
        )


@app.on_message(filters.command("acast") & filters.user(OWNER_ID))
async def announced(_, message):
    if not message.reply_to_message:
        return await message.reply_text("Yayınlamak için bir gönderiye yanıt verin.")

    to_send = message.reply_to_message.id
    users = await get_users() or [] # Veritabanından tüm kullanıcı ID'lerini al
    print(users) # Hata ayıklama için kullanıcıları yazdır
    failed_users = 0 # failed_user yerine failed_users kullanıldı (tutarlılık için)
    done_users = 0 # done_users da tanımlanmalı

    for user_id in users: # users doğrudan kullanıcı ID'lerini içeriyorsa
        try:
            await _.forward_messages(chat_id=int(user_id), from_chat_id=message.chat.id, message_ids=to_send)
            done_users += 1
            await asyncio.sleep(1) # Flood sınırı için daha uzun bir gecikme
        except Exception as e:
            failed_users += 1
            #print(f"Hata oluştu ({user_id}): {e}") # Hata ayıklama için hata basıldı

    if failed_users == 0:
        await message.reply_text( # exmsg yerine message.reply_text kullanıldı
            f"**Başarıyla yayınlandı ✅**\n\n**Mesaj gönderilen kullanıcı sayısı:** `{done_users}`"
        )
    else:
        await message.reply_text( # exmsg yerine message.reply_text kullanıldı
            f"**Başarıyla yayınlandı ✅**\n\n**Mesaj gönderilen kullanıcı sayısı:** `{done_users}`\n\n**Not:-** `Bazı sorunlar nedeniyle` `{failed_users}` **kullanıcıya yayın yapılamadı**"
        )


