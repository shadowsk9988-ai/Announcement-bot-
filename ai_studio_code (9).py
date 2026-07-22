from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db

router = Router()

@router.callback_query(F.data == "view_stats")
async def show_stats(callback: CallbackQuery):
    stats = await db.get_user_stats(callback.from_user.id)
    groups = await db.get_groups(callback.from_user.id)
    
    text = (
        "📊 **Your Statistics**\n\n"
        f"📁 Total Groups registered: {len(groups)}\n"
        f"📤 Total Messages sent: {stats[0]}\n"
        f"✅ Successful: {stats[1]}\n"
        f"❌ Failed: {stats[2]}"
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=callback.message.reply_markup)
    await callback.answer()