# ---------------------------------------------------
# File Name: start.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Adarsh
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.6
# License: MIT License
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
        await message.reply("You are not authorized to use this command.")
        return
     
    await app.set_bot_commands([
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("login", "🔑 Get into the bot"),
        BotCommand("logout", "🚪 Get out of the bot"),
        BotCommand("batch", "🫠 Extract in bulk"),
        BotCommand("cancel", "🚫 Cancel batch process"),
        BotCommand("myplan", "⌛ Get your plan details"),
        BotCommand("transfer", "💘 Gift premium to others"),
        BotCommand("settings", "⚙️ Personalize things"),
        BotCommand("speedtest", "🚅 Speed of server"),
        BotCommand("help", "❓ If you're a noob, still!"),
        BotCommand("terms", "🥺 Terms and conditions"),
        BotCommand("admin_commands_list", "📜 List of admin commands"),
        BotCommand("changemode", "🔄 Toggle free/premium mode (Owner only)"),  # Changed from freemode
        BotCommand("modecheck", "🔍 Check current mode")
    ])
 
    await message.reply("✅ Commands configured successfully!")

# Mode Toggle Commands (renamed from freemode to changemode)
@app.on_message(filters.command("changemode") & filters.user(OWNER_ID))
async def toggle_free_mode(client, message):
    """Toggle between free and premium modes"""
    from devgagan.core.mongo.plans_db import db
    current_mode = await db.bot_mode.find_one({"_id": "mode"})
    new_mode = not current_mode.get("free_mode", False) if current_mode else True
    
    await db.bot_mode.update_one(
        {"_id": "mode"},
        {"$set": {"free_mode": new_mode}},
        upsert=True
    )
    
    status = "🆓 FREE MODE (available to everyone)" if new_mode else "💰 PREMIUM MODE (subscription required)"
    await message.reply(f"Bot mode changed:\n\n{status}")

@app.on_message(filters.command("modecheck"))
async def check_mode(client, message):
    """Check current bot mode"""
    from devgagan.core.mongo.plans_db import db
    mode_data = await db.bot_mode.find_one({"_id": "mode"})
    current_mode = mode_data.get("free_mode", False) if mode_data else False
    
    status = "🆓 Currently in FREE MODE (available to everyone)" if current_mode else "💰 Currently in PREMIUM MODE (subscription required)"
    await message.reply(status)

help_pages = [
    (
        "📝 **Bot Commands Overview (1/2)**:\n\n"
        "1. **/add userID**\n"
        "> Add user to premium (Owner only)\n\n"
        "2. **/rem userID**\n"
        "> Remove user from premium (Owner only)\n\n"
        "3. **/transfer userID**\n"
        "> Transfer premium to your beloved major purpose for resellers (Premium members only)\n\n"
        "4. **/get**\n"
        "> Get all user IDs (Owner only)\n\n"
        "5. **/lock**\n"
        "> Lock channel from extraction (Owner only)\n\n"
        "6. **/dl link**\n"
        "> Download videos (Not available in v3 if you are using)\n\n"
        "7. **/adl link**\n"
        "> Download audio (Not available in v3 if you are using)\n\n"
        "8. **/login**\n"
        "> Log into the bot for private channel access\n\n"
        "9. **/batch**\n"
        "> Bulk extraction for posts (After login)\n\n"
        "19. **/changemode**\n"  # Changed from freemode
        "> Toggle between free/premium modes (Owner only)\n\n"
        "20. **/modecheck**\n"
        "> Check current mode\n\n"
    ),
    (
        "📝 **Bot Commands Overview (2/2)**:\n\n"
        "10. **/logout**\n"
        "> Logout from the bot\n\n"
        "11. **/stats**\n"
        "> Get bot stats\n\n"
        "12. **/plan**\n"
        "> Check premium plans\n\n"
        "13. **/speedtest**\n"
        "> Test the server speed (not available in v3)\n\n"
        "14. **/terms**\n"
        "> Terms and conditions\n\n"
        "15. **/cancel**\n"
        "> Cancel ongoing batch process\n\n"
        "16. **/myplan**\n"
        "> Get details about your plans\n\n"
        "17. **/session**\n"
        "> Generate Pyrogram V2 session\n\n"
        "18. **/settings**\n"
        "> 1. SETCHATID : To directly upload in channel or group or user's dm use it with -100[chatID]\n"
        "> 2. SETRENAME : To add custom rename tag or username of your channels\n"
        "> 3. CAPTION : To add custom caption\n"
        "> 4. REPLACEWORDS : Can be used for words in deleted set via REMOVE WORDS\n"
        "> 5. RESET : To set the things back to default\n\n"
        "> You can set CUSTOM THUMBNAIL, PDF WATERMARK, VIDEO WATERMARK, SESSION-based login, etc. from settings\n\n"
        "**__Powered by Adarsh__**"
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

    prev_button = InlineKeyboardButton("◀️ Previous", callback_data=f"help_prev_{page_number}")
    next_button = InlineKeyboardButton("Next ▶️", callback_data=f"help_next_{page_number}")

    buttons = []
    if page_number > 0:
        buttons.append(prev_button)
    if page_number < len(help_pages) - 1:
        buttons.append(next_button)

    keyboard = InlineKeyboardMarkup([buttons])

    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

    await message.reply(
        help_pages[page_number],
        reply_markup=keyboard
    )
 
@app.on_message(filters.command("terms") & filters.private)
async def terms(client, message):
    terms_text = (
        "> 📜 **Terms and Conditions** 📜\n\n"
        "✨ We are not responsible for user deeds, and we do not promote copyrighted content. If any user engages in such activities, it is solely their responsibility.\n"
        "✨ Upon purchase, we do not guarantee the uptime, downtime, or the validity of the plan. __Authorization and banning of users are at our discretion; we reserve the right to ban or authorize users at any time.__\n"
        "✨ Payment to us **__does not guarantee__** authorization for the /batch command. All decisions regarding authorization are made at our discretion and mood.\n"
        "✨ In FREE MODE, all features are available to everyone without restrictions.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 See Plans", callback_data="see_plan")],
            [InlineKeyboardButton("💬 Contact Now", url="https://t.me/Contact_xbot")],
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
            "> 🎉 **FREE MODE ACTIVE** 🎉\n\n"
            "✨ Currently all features are available to everyone for free!\n"
            "✨ No subscriptions or payments required at this time.\n"
            "✨ Enjoy unlimited access to all bot features.\n\n"
            "📜 **Terms and Conditions**: For details, please send /terms\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📜 See Terms", callback_data="see_terms")],
                [
                    InlineKeyboardButton("💬 Contact Support", url="https://t.me/Contact_xbot"),
                    InlineKeyboardButton("💰 Pricing Channel", url="https://t.me/+9FZJh0WMZnE4YWRk")
                ]
            ]
        )
    else:
        plan_text = (
            "> 💰 **Premium Plans**\n\n"
            "📥 **Download Limit**: Users can download up to 100,000 files in a single batch command.\n"
            "🛑 **Batch**: You will get two modes /bulk and /batch.\n"
            "   - Users are advised to wait for the process to automatically cancel before proceeding with any downloads or uploads.\n\n"
            "📜 **Check our pricing channel for current plans and offers**\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💰 Pricing Channel", url="https://t.me/+9FZJh0WMZnE4YWRk")],
                [
                    InlineKeyboardButton("📜 See Terms", callback_data="see_terms"),
                    InlineKeyboardButton("💬 Contact Support", url="https://t.me/Contact_xbot")
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
            "> 🎉 **FREE MODE ACTIVE** 🎉\n\n"
            "✨ Currently all features are available to everyone for free!\n"
            "✨ No subscriptions or payments required at this time.\n"
            "✨ Enjoy unlimited access to all bot features.\n\n"
            "📜 **Terms and Conditions**: For details, please send /terms\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📜 See Terms", callback_data="see_terms")],
                [
                    InlineKeyboardButton("💬 Contact Support", url="https://t.me/Contact_xbot"),
                    InlineKeyboardButton("💰 Pricing Channel", url="https://t.me/+9FZJh0WMZnE4YWRk")
                ]
            ]
        )
    else:
        plan_text = (
            "> 💰 **Premium Plans**\n\n"
            "📥 **Download Limit**: Users can download up to 100,000 files in a single batch command.\n"
            "🛑 **Batch**: You will get two modes /bulk and /batch.\n"
            "   - Users are advised to wait for the process to automatically cancel before proceeding with any downloads or uploads.\n\n"
            "📜 **Check our pricing channel for current plans and offers**\n"
        )
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("💰 Pricing Channel", url="https://t.me/+9FZJh0WMZnE4YWRk")],
                [
                    InlineKeyboardButton("📜 See Terms", callback_data="see_terms"),
                    InlineKeyboardButton("💬 Contact Support", url="https://t.me/Contact_xbot")
                ]
            ]
        )
    
    await callback_query.message.edit_text(plan_text, reply_markup=buttons)