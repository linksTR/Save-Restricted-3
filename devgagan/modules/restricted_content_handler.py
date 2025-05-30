import os
import json
import time
import threading
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# --- Yapılandırma ---
def get_config_value(key: str):
    try:
        with open('config.json', 'r') as f: data = json.load(f)
    except FileNotFoundError: data = {}
    return os.environ.get(key) or data.get(key, None)

# --- İlerleme Durumu Fonksiyonları ---
def downstatus_thread(bot_client: Client, statusfile: str, message_obj: Message):
    while not os.path.exists(statusfile): time.sleep(1)
    time.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r") as f: txt = f.read()
            bot_client.edit_message_text(message_obj.chat.id, message_obj.id, f"__İndiriliyor__ : **{txt}**")
            time.sleep(10)
        except Exception: time.sleep(5)

def upstatus_thread(bot_client: Client, statusfile: str, message_obj: Message):
    while not os.path.exists(statusfile): time.sleep(1)
    time.sleep(3)
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r") as f: txt = f.read()
            bot_client.edit_message_text(message_obj.chat.id, message_obj.id, f"__Yükleniyor__ : **{txt}**")
            time.sleep(10)
        except Exception: time.sleep(5)

def progress_callback(current: int, total: int, message_obj: Message, file_type: str):
    try:
        with open(f'{message_obj.id}{file_type}status.txt', "w") as f: f.write(f"{current * 100 / total:.1f}%")
    except Exception: pass

def get_message_content_type(msg: Message):
    if msg.document: return "Document"
    if msg.video: return "Video"
    if msg.animation: return "Animation"
    if msg.sticker: return "Sticker"
    if msg.voice: return "Voice"
    if msg.audio: return "Audio"
    if msg.photo: return "Photo"
    if msg.text: return "Text"
    return "Unknown"

# --- Ana Mesaj İşleyici ---
async def handle_telegram_content(bot_client: Client, message: Message, userbot_client: Client = None):
    if not message.text: return

    USAGE_GUIDE = """**GENEL SOHBETLER İÇİN**
__Sadece gönderi/gönderilerin linkini gönderin.__

**ÖZEL KANALLAR VE GRUPLAR İÇİN**
__1. Adım: Önce sohbetin davet linkini gönderin.__
__2. Adım: Ardından, istediğiniz gönderi/gönderilerin linkini gönderin.__

**BOT SOHBETLERİNDEN İÇERİK ÇEKMEK İÇİN**
__Linki '/b/', botun kullanıcı adını ve mesaj ID'sini içerecek şekilde gönderin.__
  Örnek: `https://t.me/b/TelegramBot/1234`

**ÇOKLU GÖNDERİLERİ İNDİRMEK İÇİN**
__Linkleri "başlangıç ID - bitiş ID" formatında belirtin.__
Örnek 1: `https://t.me/kanal_kullanici_adi/100-105`
Örnek 2: `https://t.me/c/kanal_numarasi/200-210`
"""

    if message.text.startswith("/start"):
        user_mention = message.from_user.mention if message.from_user else "Kullanıcı"
        await bot_client.send_message(
            message.chat.id,
            f"__👋 Merhaba **{user_mention}**, ben Kısıtlı İçerik Kaydetme Botuyum. Post linkiyle kısıtlı içerikleri size gönderebilirim.__\n\n{USAGE_GUIDE}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Kaynak Kod", url="https://github.com/bipinkrish/Save-Restricted-Bot")]]),
            reply_to_message_id=message.id
        )
        return

    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if userbot_client is None:
            await bot_client.send_message(message.chat.id, "**Userbot oturumu ayarlı değil.**", reply_to_message_id=message.id)
            return
        try:
            await userbot_client.join_chat(message.text)
            await bot_client.send_message(message.chat.id, "**Sohbete başarıyla katıldı!**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot_client.send_message(message.chat.id, "**Zaten bu sohbete katılmışsınız.**", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot_client.send_message(message.chat.id, "**Davet linki geçersiz veya süresi dolmuş.**", reply_to_message_id=message.id)
        except Exception as e:
            await bot_client.send_message(message.chat.id, f"**Sohbete katılırken hata:** __{e}__", reply_to_message_id=message.id)
        return

    if "https://t.me/" in message.text:
        parts = message.text.split('/')
        if len(parts) < 4:
            await bot_client.send_message(message.chat.id, "**Geçersiz link formatı.**", reply_to_message_id=message.id)
            return

        chat_identifier = None
        message_ids = []

        try:
            id_part = parts[-1].split('?')[0]
            if '-' in id_part:
                start_id, end_id = map(int, id_part.split('-'))
                message_ids = list(range(start_id, end_id + 1))
            else:
                message_ids = [int(id_part)]
        except ValueError:
            await bot_client.send_message(message.chat.id, "**Geçersiz mesaj ID'si formatı.**", reply_to_message_id=message.id)
            return

        is_private_channel = "https://t.me/c/" in message.text
        is_bot_chat = "https://t.me/b/" in message.text

        if is_private_channel: chat_identifier = int("-100" + parts[4])
        elif is_bot_chat: chat_identifier = parts[4]
        else: chat_identifier = parts[3]

        if chat_identifier is None:
            await bot_client.send_message(message.chat.id, "**Sohbet kimliği tanımlanamadı.**", reply_to_message_id=message.id)
            return

        if (is_private_channel or is_bot_chat) and userbot_client is None:
            await bot_client.send_message(message.chat.id, "**Userbot oturum string'i gerekiyor.**", reply_to_message_id=message.id)
            return

        for msg_id in message_ids:
            try:
                source_client = userbot_client if (is_private_channel or is_bot_chat) else bot_client
                if source_client is None:
                    await bot_client.send_message(message.chat.id, "**Gerekli istemci mevcut değil.**", reply_to_message_id=message.id)
                    break

                msg_to_copy: Message = await source_client.get_messages(chat_identifier, msg_id)

                if get_message_content_type(msg_to_copy) == "Text":
                    await bot_client.send_message(message.chat.id, msg_to_copy.text, entities=msg_to_copy.entities, reply_to_message_id=message.id)
                    continue

                smsg = await bot_client.send_message(message.chat.id, '__Medya indiriliyor... Lütfen bekleyin.__', reply_to_message_id=message.id)

                down_thread = threading.Thread(target=downstatus_thread, args=(bot_client, f'{message.id}downstatus.txt', smsg), daemon=True)
                down_thread.start()
                downloaded_file = await source_client.download_media(msg_to_copy, progress=progress_callback, progress_args=[message, "down"])
                if os.path.exists(f'{message.id}downstatus.txt'): os.remove(f'{message.id}downstatus.txt')

                up_thread = threading.Thread(target=upstatus_thread, args=(bot_client, f'{message.id}upstatus.txt', smsg), daemon=True)
                up_thread.start()

                thumb_path = None
                try:
                    if msg_to_copy.document and msg_to_copy.document.thumbs: thumb_path = await source_client.download_media(msg_to_copy.document.thumbs[-1].file_id)
                    elif msg_to_copy.video and msg_to_copy.video.thumbs: thumb_path = await source_client.download_media(msg_to_copy.video.thumbs[-1].file_id)
                    elif msg_to_copy.audio and msg_to_copy.audio.thumbs: thumb_path = await source_client.download_media(msg_to_copy.audio.thumbs[-1].file_id)
                except Exception: pass

                msg_type = get_message_content_type(msg_to_copy)
                if msg_type == "Document": await bot_client.send_document(message.chat.id, downloaded_file, thumb=thumb_path, caption=msg_to_copy.caption, caption_entities=msg_to_copy.caption_entities, reply_to_message_id=message.id, progress=progress_callback, progress_args=[message,"up"])
                elif msg_type == "Video": await bot_client.send_video(message.chat.id, downloaded_file, duration=msg_to_copy.video.duration, width=msg_to_copy.video.width, height=msg_to_copy.video.height, thumb=thumb_path, caption=msg_to_copy.caption, caption_entities=msg_to_copy.caption_entities, reply_to_message_id=message.id, progress=progress_callback, progress_args=[message,"up"])
                elif msg_type == "Animation": await bot_client.send_animation(message.chat.id, downloaded_file, reply_to_message_id=message.id)
                elif msg_type == "Sticker": await bot_client.send_sticker(message.chat.id, downloaded_file, reply_to_message_id=message.id)
                elif msg_type == "Voice": await bot_client.send_voice(message.chat.id, downloaded_file, caption=msg_to_copy.caption, caption_entities=msg_to_copy.caption_entities, reply_to_message_id=message.id, progress=progress_callback, progress_args=[message,"up"])
                elif msg_type == "Audio": await bot_client.send_audio(message.chat.id, downloaded_file, caption=msg_to_copy.caption, caption_entities=msg_to_copy.caption_entities, reply_to_message_id=message.id, progress=progress_callback, progress_args=[message,"up"])
                elif msg_type == "Photo": await bot_client.send_photo(message.chat.id, downloaded_file, caption=msg_to_copy.caption, caption_entities=msg_to_copy.caption_entities, reply_to_message_id=message.id)
                else: await bot_client.send_message(message.chat.id, "__Desteklenmeyen bir içerik türü tespit edildi.__", reply_to_message_id=message.id)

            except UsernameNotOccupied: await bot_client.send_message(message.chat.id, "**Belirtilen kullanıcı adı kimse tarafından kullanılmıyor.**", reply_to_message_id=message.id)
            except Exception as e: await bot_client.send_message(message.chat.id, f"**İçerik işlenirken hata oluştu:** __{e}__", reply_to_message_id=message.id)
            finally:
                for f_path in [downloaded_file if 'downloaded_file' in locals() else None, thumb_path, f'{message.id}upstatus.txt', f'{message.id}downstatus.txt']:
                    if f_path and os.path.exists(f_path): os.remove(f_path)
                if 'smsg' in locals():
                    try: await bot_client.delete_messages(message.chat.id, [smsg.id])
                    except Exception: pass
            time.sleep(3)

# --- İstemci Başlatma ve Çalıştırma ---
bot_client = None
userbot_client = None

def initialize_clients():
    global bot_client, userbot_client
    bot_token = get_config_value("TOKEN")
    api_hash = get_config_value("HASH")
    api_id = get_config_value("ID")

    if not all([bot_token, api_hash, api_id]):
        print("HATA: Bot token, API hash veya API ID eksik.")
        exit(1)

    bot_client = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
    ss = get_config_value("STRING")
    if ss is not None: userbot_client = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    else: print("UYARI: Userbot oturum string'i ayarlanmadı.")

@Client.on_message(filters.text & filters.private | filters.command("start"))
async def message_dispatcher(client: Client, message: Message):
    await handle_telegram_content(client, message, userbot_client)

if __name__ == "__main__":
    print("Bot başlatılıyor...")
    initialize_clients()
    try:
        if bot_client: bot_client.start(); print("Bot başlatıldı!")
        if userbot_client: userbot_client.start(); print("Userbot başlatıldı!")
        pyrogram.idle()
    except Exception as e: print(f"Bot çalışırken hata: {e}")
    finally:
        if bot_client: bot_client.stop(); print("Bot durduruldu.")
        if userbot_client: userbot_client.stop(); print("Userbot durduruldu.")
