import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from database import db

async def safe_broadcast(bot: Bot, owner_id: int, chat_id: int, content_message):
    try:
        if content_message.text:
            await bot.send_message(chat_id, content_message.text, entities=content_message.entities)
        elif content_message.photo:
            await bot.send_photo(chat_id, content_message.photo[-1].file_id, caption=content_message.caption, caption_entities=content_message.caption_entities)
        elif content_message.video:
            await bot.send_video(chat_id, content_message.video.file_id, caption=content_message.caption, caption_entities=content_message.caption_entities)
        elif content_message.forward_from_chat or content_message.forward_from:
            await bot.copy_message(chat_id, content_message.chat.id, content_message.message_id)
        
        await db.update_stats(owner_id, True)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await safe_broadcast(bot, owner_id, chat_id, content_message)
    except Exception as e:
        logging.error(f"Broadcast failed to {chat_id}: {e}")
        await db.update_stats(owner_id, False)
        return False