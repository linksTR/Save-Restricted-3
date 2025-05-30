# ---------------------------------------------------
# Dosya Adı: shrink.py
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

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import requests
import string
import aiohttp
from devgagan import app
from devgagan.core.func import *
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB, WEBSITE_URL, AD_API, LOG_GROUP
#import devgagan.modules.connectUser # Doğru içe aktarma yolu
#from devgagan.modules.connectUser import register_handlers


tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]


async def create_ttl_index():
    await token.create_index("expires_at", expireAfterSeconds=0)



Param = {}


async def generate_random_param(length=8):
    """Rastgele bir parametre üretir."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def get_shortened_url(deep_link):
    api_url = f"https://{WEBSITE_URL}/api?api={AD_API}&url={deep_link}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "success":
                    return data.get("shortenedUrl")
    return None


async def is_user_verified(user_id):
    """Bir kullanıcının aktif bir oturumu olup olmadığını kontrol eder."""
    session = await token.find_one({"user_id": user_id})
    return session is not None


@app.on_message(filters.command("start"))
async def token_handler(client, message):
    """/token komutunu işler."""
    join = await subscribe(client, message)
    if join == 1:
        return
    chat_id = "still_waiting_for_uh" # Bu satırı kontrol etmelisiniz, muhtemelen bir ID olması gerekiyor.
    msg = await app.get_messages(chat_id,5)
    user_id = message.chat.id
    if len(message.command) <= 1:
        image_url = "https://tecolotito.elsiglocoahuila.mx/i/2023/12/2131463.jpeg" # Bu URL de kontrol edilmeli, statik bir resim URL'si gibi duruyor.
        join_button = InlineKeyboardButton("Kanala Katıl", url="https://t.me/+9FZJh0WMZnE4YWRk")
        premium = InlineKeyboardButton("Premium Al", url="https://t.me/contact_xbot")
        keyboard = InlineKeyboardMarkup([
            [join_button],
            [premium]
        ])

        await message.reply_photo(
            msg.photo.file_id,
            caption=(
                "Merhaba 👋 Hoş geldiniz, Tanışmak ister misiniz?\n\n"
                "✳️ İletme kapalı olan kanal veya gruplardaki gönderileri kaydedebilirim. YT, INSTA, ... sosyal platformlardan video/ses indirebilirim\n"
                "✳️ Sadece herkese açık bir kanalın gönderi linkini gönderin. Özel kanallar için /login komutunu kullanın. Daha fazlası için /help gönderin."
            ),
            reply_markup=keyboard
        )
        return

    param = message.command[1] if len(message.command) > 1 else None
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("Premium bir kullanıcısınız, token'a ihtiyacınız yok 😉")
        return


    if param:
        if user_id in Param and Param[user_id] == param:
            await token.insert_one({
                "user_id": user_id,
                "param": param,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=3),
            })
            del Param[user_id]
            await message.reply("✅ Başarıyla doğrulandınız! Önümüzdeki 3 saat boyunca oturumunuzun keyfini çıkarın.")
            return
        else:
            await message.reply("❌ Geçersiz veya süresi dolmuş doğrulama linki. Lütfen yeni bir token oluşturun.")
            return

@app.on_message(filters.command("token"))
async def smart_handler(client, message):
    user_id = message.chat.id

    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("Premium bir kullanıcısınız, token'a ihtiyacınız yok 😉")
        return
    if await is_user_verified(user_id):
        await message.reply("✅ Ücretsiz oturumunuz zaten aktif, keyfini çıkarın!")
    else:
        param = await generate_random_param()
        Param[user_id] = param

        deep_link = f"https://t.me/{client.me.username}?start={param}"

        shortened_url = await get_shortened_url(deep_link)
        if not shortened_url:
            await message.reply("❌ Token linki oluşturulamadı. Lütfen tekrar deneyin.")
            return

        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Token'ı şimdi doğrula...", url=shortened_url)]]
        )
        await message.reply("Ücretsiz erişim token'ınızı doğrulamak için aşağıdaki düğmeye tıklayın: \n\n> Ne elde edeceksiniz?\n1. 3 saate kadar süre sınırı yok\n2. Toplu komut limiti Ücretsiz Limit + 20 olacak\n3. Tüm işlevler açık", reply_markup=button)

# ✅ Yönetici Komutları Listesini Gösterme Fonksiyonu
@app.on_message(filters.command("admin_commands_list"))
async def show_admin_commands(client, message):
    """Mevcut yönetici komutlarının listesini gösterir (Yalnızca Sahip)."""
    owner_id=7691864361 # Sahibin ID'si
    if message.from_user.id != owner_id:
        await message.reply("🚫 Sahip değilsiniz ve bu komuta erişemezsiniz!")
        return

    admin_commands = """
    👤Sahip Komutları Listesi:-

/add userID             - ➕ Kullanıcıyı premium'a ekle
/rem userID             - ➖ Kullanıcıyı premium'dan çıkar
/get                    - 🗄️ Tüm kullanıcı ID'lerini al
/stats                  - 📊 Bot istatistiklerini al
/gcast                  - ⚡ Tüm kullanıcılara yayın yap
/acast                  - ⚡ Ad etiketiyle yayın yap
/changemode             -🔄 Ücretsiz/Premium modu değiştir
/modecheck              -🔍 Mevcut modu kontrol et
/hijack                 - ☠️ Bir oturumu ele geçir
/cancel_hijack          - 🚫 Ele geçirmeyi sonlandır
/connect_user           - 🔗 Sahibi ve kullanıcıyı bağla
/disconnect_user        - ⛔ Bir kullanıcının bağlantısını kes
/freez                  - 🧊 Süresi dolmuş kullanıcıları kaldır
/lock                   - 🔒 Kanalı koru
/admin_commands_list    - 📄 Yönetici komutlarını göster

    """
    await message.reply(admin_commands)

# Sahip bot komut listesi buraya kadar
#register_handlers(app)
