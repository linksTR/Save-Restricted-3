# ---------------------------------------------------
# Dosya Adı: start.py
# Açıklama: Telegram kanallarından veya gruplarından dosya indirmek ve
# onları tekrar Telegram'a yüklemek için bir Pyrogram botu.
# Yazar: Adarsh
# Oluşturuldu: 2025-01-11
# Son Değişiklik: 2025-01-11
# Versiyon: 2.0.6
# Lisans: MIT Lisansı
# ---------------------------------------------------

from pyrogram import filters
from devgagan import app
from config import OWNER_ID
from devgagan.core.func import subscribe
import asyncio
from devgagan.core.func import *
from devgagan.modules.get import *
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.bots import SetBotInfo
from pyrogram.raw.types import InputUserSelf
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
 
@app.on_message(filters.command("set"))
async def set(_, message):
    if message.from_user.id not in OWNER_ID:
        await message.reply("kara ambar kamyoncular dernegine uye misin?")
        return
    
    await app.set_bot_commands([
        BotCommand("start", "🚀 Botu baslat"),
        BotCommand("login", "🔑 Bota giris yap"),
        BotCommand("logout", "🚪 Bottan cikis yap"),
        BotCommand("batch", "🫠 Toplu sekilde cikar"),
        BotCommand("cancel", "🚫 Toplu islemi iptal et"),
        BotCommand("myplan", "⌛ Plan detaylarinizi ogrenin"),
        BotCommand("transfer", "💘 Baska kullanicilara premium hediye et"),
        BotCommand("settings", "⚙️ Ayarlari kisisellestir"),
        BotCommand("speedtest", "🚅 Sunucu hizi testi"),
        BotCommand("help", "❓ Yardim"),
        BotCommand("terms", "🥺 Sartlar ve kosullar"),
        BotCommand("admin_commands_list", "📜 Yonetici komutlari listesi")
    ])
    await message.reply("✅ Komutlar basariyla yapilandirildi!")

# Mod Degistirme Komutlari (freemode'dan changemode'a yeniden adlandirildi)
@app.on_message(filters.command("changemode") & filters.user(OWNER_ID))
async def toggle_free_mode(client, message):
    """Ucretsiz ve premium modlar arasinda gecis yap"""
    from devgagan.core.mongo.plans_db import db
    current_mode = await db.bot_mode.find_one({"_id": "mode"})
    new_mode = not current_mode.get("free_mode", False) if current_mode else True
    
    await db.bot_mode.update_one(
        {"_id": "mode"},
        {"$set": {"free_mode": new_mode}},
        upsert=True
    )
    
    status = "🆓 UCRETSIZ MOD (herkesin erisiminde)" if new_mode else "💰 PREMIUM MOD (abonelik gereklidir)"
    await message.reply(f"Bot modu degisti:\n\n{status}")

@app.on_message(filters.command("modecheck"))
async def check_mode(client, message):
    """Mevcut bot modunu kontrol et"""
    from devgagan.core.mongo.plans_db import db
    mode_data = await db.bot_mode.find_one({"_id": "mode"})
    current_mode = mode_data.get("free_mode", False) if mode_data else False
    
    status = "🆓 Su anda UCRETSIZ MODDA (herkesin erisiminde)" if current_mode else "💰 Su anda PREMIUM MODDA (abonelik gereklidir)"
    await message.reply(status)

help_pages = [
    (
        "📝 **Bot Komutlarina Genel Bakis (1/2)**:\n\n"
        "1. **/add userID**\n"
        "> Kullaniciyi premiuma ekle (Sadece Sahip)\n\n"
        "2. **/rem userID**\n"
        "> Kullaniciyi premiumdan kaldir (Sadece Sahip)\n\n"
        "3. **/transfer userID**\n"
        "> Resellerlar icin premiumu sevdiklerinize aktarin (Sadece Premium uyeler)\n\n"
        "4. **/get**\n"
        "> Tum kullanici ID'lerini al (Sadece Sahip)\n\n"
        "5. **/lock**\n"
        "> Kanali cikarmadan kilitle (Sadece Sahip)\n\n"
        "6. **/dl link**\n"
        "> Videolari indir (Eger kullaniyorsaniz v3'te mevcut degil)\n\n"
        "7. **/adl link**\n"
        "> Ses indir (Eger kullaniyorsaniz v3'te mevcut degil)\n\n"
        "8. **/login**\n"
        "> Ozel kanal erisimi icin bota giris yap\n\n"
        "9. **/batch**\n"
        "> Gonderiler icin toplu cikarim (Giris yaptiktan sonra)\n\n"
        "19. **/changemode**\n"  # Freemode'dan degistirildi
        "> Ucretsiz/premium modlari arasinda gecis yap (Sadece Sahip)\n\n"
        "20. **/modecheck**\n"
        "> Mevcut modu kontrol et\n\n"
    ),
    (
        "📝 **Bot Komutlarina Genel Bakis (2/2)**:\n\n"
        "10. **/logout**\n"
        "> Bottan cikis yap\n\n"
        "11. **/stats**\n"
        "> Bot istatistiklerini al\n\n"
        "12. **/plan**\n"
        "> Premium planlari kontrol et\n\n"
        "13. **/speedtest**\n"
        "> Sunucu hizini test et (v3'te mevcut degil)\n\n"
        "14. **/terms**\n"
        "> Sartlar ve kosullar\n\n"
        "15. **/cancel**\n"
        "> Devam eden toplu islemi iptal et\n\n"
        "16. **/myplan**\n"
        "> Planlariniz hakkinda detayli bilgi al\n\n"
        "17. **/session**\n"
        "> Pyrogram V2 oturumu olustur\n\n"
        "18. **/settings**\n"
        "> 1. SETCHATID : Kanal, grup veya kullanici DM'sine dogrudan yuklemek icin -100[chatID] ile kullanin\n"
        "> 2. SETRENAME : Ozel yeniden adlandirma etiketi veya kanallarinizin kullanici adini eklemek icin\n"
        "> 3. CAPTION : Ozel baslik eklemek icin\n"
        "> 4. REPLACEWORDS : KALDIRILAN KELIMELER araciligiyla silinen kelimeler icin kullanilabilir\n"
        "> 5. RESET : Ayarlari varsayilana sifirlamak icin\n\n"
        "> Ayarlardan OZEL ONIZLEME, PDF FILIGRANI, VIDEO FILIGRANI, OTURUM TABANLI GIRIS vb. ayarlayabilirsiniz\n\n"
        "**__Adarsh tarafindan desteklenmektedir__**"
    )
]
 
@app.on_message(filters.command("help"))
async def help(client, message):
    join = await subscribe(client, message)
    if join == 1:
        return
    
    await send_or_edit_help_page(client, message, 0)

@app.on_callback_query(filters.regex(r"help_(prev|next)_(\d+)"))
async def on_help_navigation(client, callback_query):
    action, page_number = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])

    if action == "prev":
        page_number -= 1
    elif action == "next":
        page_number += 1

    await send_or_edit_help_page(client, callback_query.message, page_number)
    await callback_query.answer()

async def send_or_edit_help_page(_, message, page_number):
    if page_number < 0 or page_number >= len(help_pages):
        return

    if message is None:
        return

    prev_button = InlineKeyboardButton("◀️ Onceki", callback_data=f"help_prev_{page_number}")
    next_button = InlineKeyboardButton("Sonraki ▶️", callback_data=f"help_next_{page_number}")

    buttons = []
    if page_number > 0:
        buttons.append(prev_button)
    if page_number < len(help_pages) - 1:
        buttons.append(next_button)

    keyboard = InlineKeyboardMarkup([buttons])

    try:
        await message.delete()
    except Exception as e:
        print(f"Mesaj silinemedi: {e}")

    await message.reply(
        help_pages[page_number],
        reply_markup=keyboard
    )
 
@app.on_message(filters.command("terms") & filters.private)
async def terms(client, message):
    terms_text = (
        "> 📜 **Sartlar ve Kosullar** 📜\n\n"
        "✨ Kullanici eylemlerinden sorumlu degiliz ve telif hakli icerigi tesvik etmiyoruz. Eger herhangi bir kullanici bu tur faaliyetlerde bulunursa, bu tamamen kendi sorumlulugundadir.\n"
        "✨ Satin alma sonrasi, calisma suresi, durus suresi veya planin gecerliligi konusunda garanti vermiyoruz. __Kullanicilarin yetkilendirilmesi ve yasaklanmasi bizim takdirimizdedir; kullanicilari istedigimiz zaman yasaklama veya yetkilendirme hakkini sakli tutariz.__\n"
        "✨ Bize yapilan odeme, /batch komutu icin yetkilendirme **__garanti etmez__**. Yetkilendirme ile ilgili tum kararlar bizim takdirimiz ve ruh halimize gore alinir.\n"
        "✨ UCRETSIZ MOD'da, tum ozellikler herkesin erisimindedir ve herhangi bir kisitlama yoktur.\n"
    )
    
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Planlari Gor", callback_data="see_plan")],
            [InlineKeyboardButton("💬 Simdi Iletisime Gec", url="https://t.me/denujke")],
        ]
    )
    await message.reply_text(terms_text, reply_markup=buttons)
 
@app.on_message(filters.command("plan") & filters.private)
async def plan(client, message):
    from devgagan.core.mongo.plans_db import db
    mode_data = await db.bot_mode.find_one({"_id": "mode"})
    current_mode = mode_data.get("free_mode", False) if mode_data else False
    
    if current_mode:
        plan_text = (
            "> 🎉 **UCRETSIZ MOD AKTIF** 🎉\n\n"
            "✨ Su anda tum ozellikler herkese ucretsiz olarak sunulmaktadir!\n"
            "✨ Bu sure zarfinda abonelik veya odeme gerekmemektedir.\n"
            "✨ Tum bot ozelliklerine sinirsiz erisimin tadini cikarin.\n\n"
            "📜 **Sartlar ve Kosullar**: Detaylar icin lutfen /terms gonderin\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📜 Sartlari Gor", callback_data="see_terms")],
                [
                    InlineKeyboardButton("💬 Destekle Iletisime Gec", url="https://t.me/denujke"),
                    InlineKeyboardButton("💰 Fiyatlandirma Kanali", url="https://t.me/denujke")
                ]
            ]
        )
    else:
        plan_text = (
            "> 💰 **Premium Planlar**\n\n"
            "📥 **Indirme Limiti**: Kullanicilar tek bir toplu komutta 100.000 dosyaya kadar indirebilir.\n"
            "🛑 **Toplu Islem**: Iki modunuz olacak /bulk ve /batch.\n"
            "   - Kullanicilarin, herhangi bir indirme veya yukleme islemine baslamadan once islemin otomatik olarak iptal olmasini beklemesi tavsiye edilir.\n\n"
            "📜 **Mevcut planlar ve teklifler icin fiyatlandirma kanalimizi kontrol edin**\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💰 Fiyatlandirma Kanali", url="https://t.me/denujke")],
                [
                    InlineKeyboardButton("📜 Sartlari Gor", callback_data="see_terms"),
                    InlineKeyboardButton("💬 Destekle Iletisime Gec", url="https://t.me/denujke")
                ]
            ]
        )
    
    await message.reply_text(plan_text, reply_markup=buttons)

@app.on_callback_query(filters.regex("see_plan"))
async def see_plan(client, callback_query):
    from devgagan.core.mongo.plans_db import db
    mode_data = await db.bot_mode.find_one({"_id": "mode"})
    current_mode = mode_data.get("free_mode", False) if mode_data else False
    
    if current_mode:
        plan_text = (
            "> 🎉 **UCRETSIZ MOD AKTIF** 🎉\n\n"
            "✨ Su anda tum ozellikler herkese ucretsiz olarak sunulmaktadir!\n"
            "✨ Bu sure zarfinda abonelik veya odeme gerekmemektedir.\n"
            "✨ Tum bot ozelliklerine sinirsiz erisimin tadini cikarin.\n\n"
            "📜 **Sartlar ve Kosullar**: Detaylar icin lutfen /terms gonderin\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📜 Sartlari Gor", callback_data="see_terms")],
                [
                    InlineKeyboardButton("💬 Destekle Iletisime Gec", url="https://t.me/denujke"),
                    InlineKeyboardButton("💰 Fiyatlandirma Kanali", url="https://t.me/denujke")
                ]
            ]
        )
    else:
        plan_text = (
            "> 💰 **Premium Planlar**\n\n"
            "📥 **Indirme Limiti**: Kullanicilar tek bir toplu komutta 100.000 dosyaya kadar indirebilir.\n"
            "🛑 **Toplu Islem**: Iki modunuz olacak /bulk ve /batch.\n"
            "   - Kullanicilarin, herhangi bir indirme veya yukleme islemine baslamadan once islemin otomatik olarak iptal olmasini beklemesi tavsiye edilir.\n\n"
            "📜 **Mevcut planlar ve teklifler icin fiyatlandirma kanalimizi kontrol edin**\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💰 Fiyatlandirma Kanali", url="https://t.me/denujke")],
                [
                    InlineKeyboardButton("📜 Sartlari Gor", callback_data="see_terms"),
                    InlineKeyboardButton("💬 Destekle Iletisime Gec", url="https://t.me/denujke")
                ]
            ]
        )
    
    await callback_query.message.edit_text(plan_text, reply_markup=buttons)
 
