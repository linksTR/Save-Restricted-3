# ---------------------------------------------------
# File Name: main.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Adarsh
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# More readable 
# ---------------------------------------------------

import time
import random
import string
import asyncio
# modules/main.py

import time
import random
import string
import asyncio
from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Kendi yeni modüllerimizi içe aktarıyoruz
from modules.config import Config as RestrictedModuleConfig # Çakışmayı önlemek için farklı isim
from modules.restricted_content_handler import handle_restricted_content # Ana işleyici fonksiyon

# Mevcut devgagan import'ları (değişmedi)
from devgagan import app # Ana Pyrogram bot objesi
from config import API_ID, API_HASH, FREEMIUM_LIMIT, PREMIUM_LIMIT, OWNER_ID # Ana dizindeki config
from devgagan.core.get_func import get_msg
from devgagan.core.func import *
from devgagan.core.mongo import db
from devgagan.core.mongo.db import user_sessions_real
import subprocess
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from devgagan.modules.shrink import is_user_verified

# Global değişkenler (değişmedi)
users_loop = {}
interval_set = {}
batch_mode = {}

# Userbot istemcisini global olarak tanımla
# Bu, app.py veya botun başlangıcında başlatılacak ve handler'lara iletilecek
global_userbot_client = None # Bot başlatıldığında atanacak

# Diğer yardımcı fonksiyonlar (initialize_userbot, process_and_upload_link, check_interval, set_interval, is_normal_tg_link, process_special_links)
# aynı kalabilir.
# Ancak `process_special_links` fonksiyonunun içeriği artık `handle_restricted_content` içinde olduğundan,
# bu fonksiyonun içini boşaltabilir veya kaldırabilirsin.

# Önemli: `process_special_links` fonksiyonunu kaldırıyoruz veya içini boşaltıyoruz
# çünkü tüm link işleme `handle_restricted_content` tarafından yapılacak.
async def process_special_links(userbot, user_id, msg, link):
    """
    Bu fonksiyonun içeriği artık handle_restricted_content tarafından yönetildiği için
    bu fonksiyonu kaldırabiliriz veya içini boşaltabiliriz.
    """
    pass # Boş bırakıldı, eğer hala bir yerde çağrılıyorsa silmek yerine boş bırakmak daha güvenli.
from pyrogram import filters, Client
from devgagan import app
from config import API_ID, API_HASH, FREEMIUM_LIMIT, PREMIUM_LIMIT, OWNER_ID
from devgagan.core.get_func import get_msg
from devgagan.core.func import *
from devgagan.core.mongo import db
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from devgagan.core.mongo.db import user_sessions_real
import subprocess
from pyrogram.handlers import MessageHandler, CallbackQueryHandler


from devgagan.modules.shrink import is_user_verified
async def generate_random_name(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

# Global dictionaries to track user states
users_loop = {}      # Tracks users currently processing
interval_set = {}    # Tracks user cooldown intervals
batch_mode = {}      # Tracks users in batch mode


async def process_and_upload_link(userbot, user_id, msg_id, link, retry_count, message):
    try:
        await get_msg(userbot, user_id, msg_id, link, retry_count, message)
        await asyncio.sleep(15)
    finally:
        pass

# Function to check if the user can proceed
async def check_interval(user_id, freecheck):
    if freecheck != 1 or await is_user_verified(user_id):  # Premium or owner users can always proceed
        return True, None

    now = datetime.now()

    # Check if the user is on cooldown
    if user_id in interval_set:
        cooldown_end = interval_set[user_id]
        if now < cooldown_end:
            remaining_time = (cooldown_end - now).seconds
            return False, f"Please wait {remaining_time} seconds(s) before sending another link. Alternatively, purchase premium for instant access.\n\n>"
        else:
            del interval_set[user_id]  # Cooldown expired, remove user from interval set

    return True, None

async def set_interval(user_id, interval_minutes=45):
    now = datetime.now()
    # Set the cooldown interval for the user
    interval_set[user_id] = now + timedelta(seconds=interval_minutes)
    

@app.on_message(
    filters.regex(r'https?://(?:www\.)?t\.me/[^\s]+|tg://openmessage\?user_id=\w+&message_id=\d+')
    & filters.private
)
async def single_link(_, message):
    """Handle single link processing"""
    user_id = message.chat.id
    is_free_mode = await check_bot_mode()  # Check current mode

    # Check subscription and batch mode
    if await subscribe(_, message) == 1 or user_id in batch_mode:
        return

    # Check if user is already in a loop
    if users_loop.get(user_id, False):
        await message.reply(
            "You already have an ongoing process. Please wait for it to finish or cancel it with /cancel."
        )
        return

    # Check freemium limits with mode-specific messaging
    if await chk_user(message, user_id) == 1 and FREEMIUM_LIMIT == 0 and user_id not in OWNER_ID and not await is_user_verified(user_id):
        if is_free_mode:
            await message.reply("🎉 Free Mode Active! Enjoy unlimited access to all features!")
        else:
            await message.reply("Freemium service is currently not available. Upgrade to premium for access.")
        return

    # Check cooldown (respects free mode)
    can_proceed, response_message = await check_interval(user_id, await chk_user(message, user_id))
    if not can_proceed:
        await message.reply(response_message)
        return

    # Add user to processing loop
    users_loop[user_id] = True
    link = message.text if "tg://openmessage" in message.text else get_link(message.text)
    msg = await message.reply("Processing...")
    userbot = await initialize_userbot(user_id)

    try:
        if await is_normal_tg_link(link):
            # Handle normal Telegram links
            await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
            await set_interval(user_id, interval_minutes=45)
        else:
            # Handle special Telegram links
            await process_special_links(userbot, user_id, msg, link)
            
    except FloodWait as fw:
        await msg.edit_text(f'Try again after {fw.x} seconds due to floodwait from Telegram.')
    except Exception as e:
        await msg.edit_text(f"Link: `{link}`\n\n**Error:** {str(e)}")
    finally:
        # Cleanup
        users_loop[user_id] = False
        if userbot:
            await userbot.stop()
        try:
            await msg.delete()
        except Exception:
            pass
# modules/main.py

# ---------------------------------------------------
# File Name: main.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Adarsh
# Created: 2025-01-11
# Last Modified: 2025-05-31 (Entegre Edilmiş Sürüm)
# Version: 2.0.5
# License: MIT License
# More readable 
# ---------------------------------------------------

import time
import random
import string
import asyncio

from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Kendi yeni modüllerimizi içe aktarıyoruz
# RestrictedModuleConfig: Kısıtlı içerik modülüne özel yapılandırma ayarları
from modules.config import Config as RestrictedModuleConfig 
# handle_restricted_content: Kısıtlı içerik linklerini işleyen ana fonksiyon
from modules.restricted_content_handler import handle_restricted_content 

# Mevcut devgagan import'ları
from devgagan import app # Ana Pyrogram bot objesi
# Ana dizindeki config'den gelen temel ayarlar.
# DİKKAT: Bu değişkenler (API_ID, API_HASH vb.) RestrictedModuleConfig ile çakışabilir.
# Eğer modül için ayrı değerler tanımlıysa, modül kendi config'ini kullanır.
from config import API_ID, API_HASH, FREEMIUM_LIMIT, PREMIUM_LIMIT, OWNER_ID 

from devgagan.core.get_func import get_msg
from devgagan.core.func import * # check_bot_mode, chk_user, subscribe, get_link, userbot_join gibi yardımcı fonksiyonlar
from devgagan.core.mongo import db
from devgagan.core.mongo.db import user_sessions_real
import subprocess
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from devgagan.modules.shrink import is_user_verified

# Global değişkenler
users_loop = {}      # İşlemde olan kullanıcıları takip eder
interval_set = {}    # Kullanıcıların bekleme sürelerini takip eder
batch_mode = {}      # Toplu işlem modundaki kullanıcıları takip eder

# Userbot istemcisini global olarak tanımla
# Bu, app.py veya botun başlangıcında başlatılacak ve handler'lara iletilecek
global_userbot_client = None # Bot başlatıldığında atanacak

# Yardımcı Fonksiyonlar (Mevcut yapıdan korunmuştur)

async def generate_random_name(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

async def initialize_userbot(user_id):
    """
    Kullanıcı için userbot oturumunu başlatır veya mevcut olanı döndürür.
    Tekli başlatmayı sağlar ve bağlı istemciyi yeniden kullanır.
    """
    global global_userbot_client 

    # Mevcut global userbot bağlıysa, onu kullan
    if global_userbot_client is not None and global_userbot_client.is_connected:
        return global_userbot_client

    # Kullanıcıya özel oturum string'i ara
    data = await db.get_data(user_id)
    session_string_to_use = None
    if data and data.get("session"):
        session_string_to_use = data.get("session")
    else:
        # Kullanıcıya özel oturum yoksa, modülün genel userbot oturumunu kullan
        session_string_to_use = RestrictedModuleConfig.USERBOT_SESSION_STRING

    if session_string_to_use:
        try:
            device = 'iPhone 16 Pro' 
            global_userbot_client = Client( 
                f"userbot_{user_id}", 
                api_id=RestrictedModuleConfig.API_ID, 
                api_hash=RestrictedModuleConfig.API_HASH, 
                device_model=device,
                session_string=session_string_to_use
            )
            await global_userbot_client.start()
            print(f"Userbot oturumu {user_id} için başlatıldı!")
            return global_userbot_client
        except Exception as e:
            print(f"Userbot başlatılırken hata: {e}")
            global_userbot_client = None 
            return None
    return None 

async def process_and_upload_link(userbot, user_id, msg_id, link, retry_count, message):
    try:
        await get_msg(userbot, user_id, msg_id, link, retry_count, message)
        await asyncio.sleep(15)
    finally:
        pass

async def check_interval(user_id, freecheck):
    if freecheck != 1 or await is_user_verified(user_id):
        return True, None
    now = datetime.now()
    if user_id in interval_set:
        cooldown_end = interval_set[user_id]
        if now < cooldown_end:
            remaining_time = (cooldown_end - now).seconds
            return False, f"Please wait {remaining_time} seconds(s) before sending another link. Alternatively, purchase premium for instant access.\n\n>"
        else:
            del interval_set[user_id]
    return True, None

async def set_interval(user_id, interval_minutes=45):
    now = datetime.now()
    interval_set[user_id] = now + timedelta(seconds=interval_minutes)

async def is_normal_tg_link(link: str) -> bool:
    """Linkin standart bir Telegram linki olup olmadığını kontrol eder."""
    special_identifiers = ['t.me/+', 't.me/c/', 't.me/b/', 'tg://openmessage']
    return 't.me/' in link and not any(x in link for x in special_identifiers)

# `process_special_links` fonksiyonu kaldırıldı/içi boşaltıldı,
# çünkü `handle_restricted_content` tüm bu mantığı üstleniyor.
async def process_special_links(userbot, user_id, msg, link):
    pass


# --- Mesaj İşleyicileri ---

# `/start` komutu için işleyici.
# Bu işleyici, hem genel `/start` mesajını hem de kısıtlı içerik modülünün kullanım kılavuzunu sağlar.
@app.on_message(filters.command("start") & filters.private)
async def start_command_for_restricted_module(_, message):
    # Kısıtlı içerik işleyicisini çağır
    # Bu, modülün kendi /start yanıtını vermesini sağlar.
    await handle_restricted_content(app, message, global_userbot_client)


# Link işleme için ana işleyici.
# Hem normal Telegram linklerini hem de özel/kısıtlı linkleri `handle_restricted_content`'a yönlendirir.
@app.on_message(
    filters.regex(r'https?://(?:www\.)?t\.me/[^\s]+|tg://openmessage\?user_id=\w+&message_id=\d+')
    & filters.private
)
async def single_link(_, message: Message): # Message type hint eklendi
    """
    Tekli link işleme işlemini `handle_restricted_content`'a yönlendirir.
    Bu, `single_link` ve `process_special_links`'in önceki mantığını değiştirir.
    """
    user_id = message.chat.id
    is_free_mode = await check_bot_mode() 

    # Abonelik ve toplu mod kontrolleri
    if await subscribe(_, message) == 1 or user_id in batch_mode:
        return

    # Kullanıcının zaten bir işlemde olup olmadığını kontrol et
    if users_loop.get(user_id, False):
        await message.reply(
            "Zaten devam eden bir işleminiz var. Lütfen bitmesini bekleyin veya /cancel ile iptal edin."
        )
        return

    # Freemium limit kontrolleri
    if await chk_user(message, user_id) == 1 and RestrictedModuleConfig.FREEMIUM_LIMIT == 0 and user_id not in RestrictedModuleConfig.OWNER_ID and not await is_user_verified(user_id):
        if is_free_mode:
            await message.reply("🎉 Ücretsiz Mod Aktif! Tüm özelliklere sınırsız erişimin keyfini çıkarın!")
        else:
            await message.reply("Freemium hizmeti şu anda kullanılamıyor. Erişim için premium'a yükseltin.")
        return

    # Bekleme süresi (cooldown) kontrolü
    can_proceed, response_message = await check_interval(user_id, await chk_user(message, user_id))
    if not can_proceed:
        await message.reply(response_message)
        return

    # Kullanıcıyı işlem döngüsüne ekle
    users_loop[user_id] = True
    
    # Userbot'ı başlat veya mevcut olanı al
    userbot_instance = await initialize_userbot(user_id)
    
    # Eğer özel/bot kanalı veya tg://openmessage linki ise ve userbot yoksa hata ver
    if not userbot_instance and ("https://t.me/c/" in message.text or "https://t.me/b/" in message.text or "tg://openmessage" in message.text):
        await message.reply("Bu tür içerik için userbot oturumu gerekiyor. Lütfen botta oturum açın.")
        users_loop[user_id] = False
        return

    try:
        # Tüm link işleme mantığını `handle_restricted_content`'a devret
        await handle_restricted_content(app, message, userbot_instance)
        await set_interval(user_id, interval_minutes=45) # İşlem başarılıysa bekleme süresi ayarla
    except FloodWait as fw:
        await message.reply(f'Telegram\'dan gelen floodwait nedeniyle {fw.x} saniye sonra tekrar deneyin.')
    except Exception as e:
        await message.reply(f"Link: `{message.text}`\n\n**Hata:** {str(e)}")
    finally:
        # Temizleme
        users_loop[user_id] = False
        # `handle_restricted_content` fonksiyonu mesaj silme işlemlerini kendi içinde yönetir.


# `/batch` komutu için işleyici.
# Toplu link işleme mantığını `handle_restricted_content`'a yönlendirir.
@app.on_message(filters.command("batch") & filters.private)
async def batch_link(_, message: Message): # Message type hint eklendi
    join = await subscribe(_, message)
    if join == 1:
        return
    user_id = message.chat.id
    
    # Toplu işlemin zaten çalışıp çalışmadığını kontrol et
    if users_loop.get(user_id, False):
        await app.send_message(
            message.chat.id,
            "Zaten devam eden bir toplu işleminiz var. Lütfen bitmesini bekleyin."
        )
        return

    freecheck = await chk_user(message, user_id)
    # Freemium limit kontrolü
    if freecheck == 1 and RestrictedModuleConfig.FREEMIUM_LIMIT == 0 and user_id not in RestrictedModuleConfig.OWNER_ID and not await is_user_verified(user_id):
        await message.reply("Freemium hizmeti şu anda kullanılamıyor. Erişim için premium'a yükseltin.")
        return

    max_batch_size = RestrictedModuleConfig.FREEMIUM_LIMIT if freecheck == 1 else RestrictedModuleConfig.PREMIUM_LIMIT

    # Başlangıç linki girişi
    for attempt in range(3):
        start = await app.ask(message.chat.id, "Lütfen başlangıç linkini gönderin.\n\n> Maksimum deneme 3")
        start_id = start.text.strip()
        s = start_id.split("/")[-1]
        if s.isdigit():
            cs = int(s)
            break
        await app.send_message(message.chat.id, "Geçersiz link. Lütfen tekrar gönderin ...")
    else:
        await app.send_message(message.chat.id, "Maksimum deneme aşıldı. Daha sonra tekrar deneyin.")
        return

    # Mesaj sayısı girişi
    for attempt in range(3):
        num_messages = await app.ask(message.chat.id, f"Kaç mesaj işlemek istersiniz?\n> Maksimum limit {max_batch_size}")
        try:
            cl = int(num_messages.text.strip())
            if 1 <= cl <= max_batch_size:
                break
            raise ValueError()
        except ValueError:
            await app.send_message(
                message.chat.id, 
                f"Geçersiz sayı. Lütfen 1 ile {max_batch_size} arasında bir sayı girin."
            )
    else:
        await app.send_message(message.chat.id, "Maksimum deneme aşıldı. Daha sonra tekrar deneyin.")
        return

    # Doğrulama ve bekleme süresi kontrolü
    can_proceed, response_message = await check_interval(user_id, freecheck)
    if not can_proceed:
        await message.reply(response_message)
        return
        
    join_button = InlineKeyboardButton("Kanala Katıl", url="https://t.me/+9FZJh0WMZnE4YWRk")
    keyboard = InlineKeyboardMarkup([[join_button]])
    pin_msg = await app.send_message(
        user_id,
        f"Toplu işlem başlatıldı ⚡\nİşleniyor: 0/{cl}\n\n****",
        reply_markup=keyboard
    )
    await pin_msg.pin(both_sides=True)

    users_loop[user_id] = True
    try:
        # Userbot'ı başlatma (global_userbot_client'ı kullanacağız)
        userbot_instance = await initialize_userbot(user_id)
        if not userbot_instance:
            await app.send_message(message.chat.id, "Lütfen önce bota giriş yapın veya bir oturum dizisi sağlayın ...")
            users_loop[user_id] = False
            return
            
        # Batch işlemi sırasında her linki handle_restricted_content ile işle
        for i in range(cs, cs + cl):
            if user_id in users_loop and users_loop[user_id]:
                url = f"{'/'.join(start_id.split('/')[:-1])}/{i}"
                
                # `handle_restricted_content` fonksiyonu bir Pyrogram `Message` objesi beklediği için,
                # toplu işlemdeki her URL için sahte (dummy) bir `Message` objesi oluşturulur.
                dummy_message = Message(
                    id=message.id, # Orijinal mesajın ID'si
                    chat={"id": message.chat.id}, # Orijinal mesajın sohbet bilgisi
                    text=url, # İşlenecek URL
                    date=datetime.now() # Geçerli tarih
                )
                
                # `handle_restricted_content`'ı çağır
                await handle_restricted_content(app, dummy_message, userbot_instance)
                
                await pin_msg.edit_text(
                    f"Toplu işlem başlatıldı ⚡\nİşleniyor: {i - cs + 1}/{cl}\n\n****",
                    reply_markup=keyboard
                )

        await set_interval(user_id, interval_minutes=300)
        await pin_msg.edit_text(
            f"Toplu işlem {cl} mesaj için başarıyla tamamlandı 🎉\n\n****",
            reply_markup=keyboard
        )
        await app.send_message(message.chat.id, "Toplu işlem başarıyla tamamlandı! 🎉")

    except Exception as e:
        await app.send_message(message.chat.id, f"Hata: {e}")
    finally:
        users_loop.pop(user_id, None)

# `/cancel` komutu için işleyici.
@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id

    # Kullanıcı için aktif bir toplu işlem olup olmadığını kontrol et
    if user_id in users_loop and users_loop[user_id]:
        users_loop[user_id] = False # Döngü durumunu False yap
        await app.send_message(
            message.chat.id, 
            "Toplu işlem başarıyla durduruldu. Dilerseniz yeni bir toplu işlem başlatabilirsiniz."
        )
    elif user_id in users_loop and not users_loop[user_id]:
        await app.send_message(
            message.chat.id, 
            "Toplu işlem zaten durdurulmuştu. İptal edilecek aktif bir işlem yok."
        )
    else:
        await app.send_message(
            message.chat.id, 
            "İptal edilecek aktif bir toplu işlem çalışmıyor."
        )


