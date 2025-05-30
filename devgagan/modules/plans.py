# ---------------------------------------------------
# Dosya Adı: plans.py
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

from datetime import timedelta
import pytz
import datetime, time
from devgagan import app
import asyncio
from config import OWNER_ID
from devgagan.core.func import get_seconds
from devgagan.core.mongo import plans_db
from pyrogram import filters


@app.on_message(filters.command("rem") & filters.user(OWNER_ID))
async def remove_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await plans_db.check_premium(user_id)

        if data and data.get("_id"):
            await plans_db.remove_premium(user_id)
            await message.reply_text("Kullanıcı başarıyla kaldırıldı!")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Merhaba {user.mention},\n\nPremium erişiminiz kaldırıldı.\nHizmetimizi kullandığınız için teşekkür ederiz 😊.</b>"
            )
        else:
            await message.reply_text("Kullanıcı kaldırılamadı!\nPremium bir kullanıcı olduğundan emin misiniz?")
    else:
        await message.reply_text("Kullanım: /rem kullanıcı_id")


@app.on_message(filters.command("myplan"))
async def myplan(client, message):
    user_id = message.from_user.id
    user = message.from_user.mention
    data = await plans_db.check_premium(user_id)
    if data and data.get("expire_date"):
        expiry = data.get("expire_date")
        expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
        expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ SÜRE BİTİM SAATİ: %I:%M:%S %p")

        current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
        time_left = expiry_ist - current_time


        days = time_left.days
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)


        time_left_str = f"{days} GÜN, {hours} SAAT, {minutes} DAKİKA"
        await message.reply_text(f"⚜️ PREMIUM KULLANICI BİLGİLERİ:\n\n👤 KULLANICI: {user}\n⚡ KULLANICI ID: {user_id}\n⏰ KALAN SÜRE: {time_left_str}\n⌛️ SON KULLANMA TARİHİ: {expiry_str_in_ist}")
    else:
        await message.reply_text(f"Merhaba {user},\n\nHerhangi bir aktif premium planınız bulunmamaktadır.")


@app.on_message(filters.command("check") & filters.user(OWNER_ID))
async def get_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await plans_db.check_premium(user_id)
        if data and data.get("expire_date"):
            expiry = data.get("expire_date")
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ SÜRE BİTİM SAATİ: %I:%M:%S %p")

            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
            time_left = expiry_ist - current_time


            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)


            time_left_str = f"{days} gün, {hours} saat, {minutes} dakika"
            await message.reply_text(f"⚜️ PREMIUM KULLANICI BİLGİLERİ:\n\n👤 KULLANICI: {user.mention}\n⚡ KULLANICI ID: {user_id}\n⏰ KALAN SÜRE: {time_left_str}\n⌛️ SON KULLANMA TARİHİ: {expiry_str_in_ist}")
        else:
            await message.reply_text("Veritabanında bu kullanıcıya ait premium veri bulunamadı!")
    else:
        await message.reply_text("Kullanım: /check kullanıcı_id")


@app.on_message(filters.command("add") & filters.user(OWNER_ID))
async def give_premium_cmd_handler(client, message):
    if len(message.command) == 4:
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ KATILIM SAATİ: %I:%M:%S %p")
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        time = message.command[2]+" "+message.command[3]
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await plans_db.add_premium(user_id, expiry_time)
            data = await plans_db.check_premium(user_id)
            expiry = data.get("expire_date")
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ SÜRE BİTİM SAATİ: %I:%M:%S %p") # Bu saat dilimini değiştirmek isteyebilirsiniz.
            await message.reply_text(f"PREMIUM BAŞARIYLA EKLENDİ ✅\n\n👤 KULLANICI: {user.mention}\n⚡ KULLANICI ID: {user_id}\n⏰ PREMIUM ERİŞİM SÜRESİ: <code>{time}</code>\n\n⏳ KATILIM TARİHİ: {current_time}\n\n⌛️ SON KULLANMA TARİHİ: {expiry_str_in_ist} \n\n__****", disable_web_page_preview=True)
            await client.send_message(
                chat_id=user_id,
                text=f"👋 Merhaba {user.mention},\nPremium satın aldığınız için teşekkür ederiz.\nKeyfini çıkarın!! ✨🎉\n\n⏰ PREMIUM ERİŞİM SÜRESİ: {time}\n⏳ KATILIM TARİHİ: {current_time}\n\n⌛️ SON KULLANMA TARİHİ: {expiry_str_in_ist}", disable_web_page_preview=True
            )

        else:
            await message.reply_text("Geçersiz zaman formatı. Lütfen '1 day', '1 hour', '1 min', '1 month' veya '1 year' şeklinde kullanın.")
    else:
        await message.reply_text("Kullanım: /add kullanıcı_id süre (örneğin, '1 day' günler için, '1 hour' saatler için, '1 min' dakikalar için, '1 month' aylar için veya '1 year' yıl için)")


@app.on_message(filters.command("transfer"))
async def transfer_premium(client, message):
    if len(message.command) == 2:
        new_user_id = int(message.command[1])  # Premium'un aktarılacağı kullanıcı ID'si
        sender_user_id = message.from_user.id  # Komutu veren mevcut premium kullanıcı
        sender_user = await client.get_users(sender_user_id)
        new_user = await client.get_users(new_user_id)

        # Göndericinin premium plan detaylarını getir
        data = await plans_db.check_premium(sender_user_id)

        if data and data.get("_id"):  # Göndericinin zaten premium kullanıcı olduğunu doğrula
            expiry = data.get("expire_date")

            # Göndericinin premiumunu kaldır
            await plans_db.remove_premium(sender_user_id)

            # Yeni kullanıcıya aynı sona erme tarihiyle premium ekle
            await plans_db.add_premium(new_user_id, expiry)

            # Sona erme tarihini göstermek için IST formatına dönüştür
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime( # Bu saat dilimini değiştirmek isteyebilirsiniz.
                "%d-%m-%Y\n⏱️ **Süre Bitim Saati:** %I:%M:%S %p"
            )
            time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata")) # Bu saat dilimini değiştirmek isteyebilirsiniz.
            current_time = time_zone.strftime("%d-%m-%Y\n⏱️ **Transfer Saati:** %I:%M:%S %p")

            # Göndericiye onay mesajı
            await message.reply_text(
                f"✅ **Premium Plan Başarıyla Aktarıldı!**\n\n"
                f"👤 **Kimden:** {sender_user.mention}\n"
                f"👤 **Kime:** {new_user.mention}\n"
                f"⏳ **Son Kullanma Tarihi:** {expiry_str_in_ist}\n\n"
                f"__Her türlü soru için @Contact_xbot__ 🚀"
            )

            # Yeni kullanıcıya bildirim
            await client.send_message(
                chat_id=new_user_id,
                text=(
                    f"👋 **Merhaba {new_user.mention},**\n\n"
                    f"🎉 **Premium Planınız Aktarıldı!**\n"
                    f"🛡️ **Aktaran:** {sender_user.mention}\n\n"
                    f"⏳ **Son Kullanma Tarihi:** {expiry_str_in_ist}\n"
                    f"📅 **Aktarım Tarihi:** {current_time}\n\n"
                    f"__Hizmetin Keyfini Çıkarın!__ ✨"
                )
            )
        else:
            await message.reply_text("⚠️ **Premium kullanıcı değilsiniz!**\n\nSadece Premium kullanıcılar planlarını aktarabilir.")
    else:
        await message.reply_text("⚠️ **Kullanım:** /transfer kullanıcı_id\n\n`kullanıcı_id` yerine yeni kullanıcının ID'sini yazın.")


async def premium_remover():
    all_users = await plans_db.premium_users()
    removed_users = []
    not_removed_users = []

    for user_id in all_users:
        try:
            user = await app.get_users(user_id)
            chk_time = await plans_db.check_premium(user_id)

            if chk_time and chk_time.get("expire_date"):
                expiry_date = chk_time["expire_date"]

                if expiry_date <= datetime.datetime.now():
                    name = user.first_name
                    await plans_db.remove_premium(user_id)
                    await app.send_message(user_id, text=f"Merhaba {name}, premium aboneliğiniz sona erdi.")
                    print(f"{name}, premium aboneliğiniz sona erdi.")
                    removed_users.append(f"{name} ({user_id})")
                else:
                    name = user.first_name
                    current_time = datetime.datetime.now()
                    time_left = expiry_date - current_time

                    days = time_left.days
                    hours, remainder = divmod(time_left.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    if days > 0:
                        remaining_time = f"{days} gün, {hours} saat, {minutes} dakika, {seconds} saniye"
                    elif hours > 0:
                        remaining_time = f"{hours} saat, {minutes} dakika, {seconds} saniye"
                    elif minutes > 0:
                        remaining_time = f"{minutes} dakika, {seconds} saniye"
                    else:
                        remaining_time = f"{seconds} saniye"

                    print(f"{name} : Kalan Süre : {remaining_time}")
                    not_removed_users.append(f"{name} ({user_id})")
        except:
            await plans_db.remove_premium(user_id)
            print(f"Bilinmeyen kullanıcılar yakalandı: {user_id} kaldırıldı")
            removed_users.append(f"Bilinmeyen ({user_id})")

    return removed_users, not_removed_users


@app.on_message(filters.command("freez") & filters.user(OWNER_ID))
async def refresh_users(_, message):
    removed_users, not_removed_users = await premium_remover()
    # Bir özet mesajı oluştur
    removed_text = "\n".join(removed_users) if removed_users else "Kaldırılan kullanıcı yok."
    not_removed_text = "\n".join(not_removed_users) if not_removed_users else "Premium'u kalan kullanıcı yok."
    summary = (
        f"**İşte Özet...**\n\n"
        f"> **Kaldırılan Kullanıcılar:**\n{removed_text}\n\n"
        f"> **Kaldırılmayan Kullanıcılar:**\n{not_removed_text}"
    )
    await message.reply(summary)
