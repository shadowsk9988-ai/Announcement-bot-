from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database import db
from states import BroadcastStates
from keyboards import broadcast_confirm_kb
from utils import safe_broadcast

router = Router()

@router.callback_query(F.data == "broadcast_start")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    selected_groups = await db.get_selected_groups(callback.from_user.id)
    if not selected_groups:
        await callback.answer("❌ No groups selected! Go to 'My Groups' first.", show_alert=True)
        return
    
    await state.set_state(BroadcastStates.waiting_for_content)
    await callback.message.edit_text(
        f"📢 **Creating Announcement**\n\n"
        f"Target: {len(selected_groups)} groups.\n\n"
        "Please send the message you want to broadcast.\n"
        "Supports: Text, Photo, Video (max 20s), or Forwarded messages.",
        parse_mode="Markdown"
    )

@router.message(BroadcastStates.waiting_for_content)
async def preview_broadcast(message: Message, state: FSMContext):
    # Handling Video Duration
    if message.video and message.video.duration > 20:
        await message.answer("❌ Video is too long (max 20 seconds).")
        return

    await state.update_data(broadcast_msg=message)
    await message.answer("👆 This is your message. Confirm to send?", reply_markup=broadcast_confirm_kb())
    await state.set_state(BroadcastStates.confirm_broadcast)

@router.callback_query(F.data == "broadcast_confirm", BroadcastStates.confirm_broadcast)
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg: Message = data.get("broadcast_msg")
    owner_id = callback.from_user.id
    
    selected_groups = await db.get_selected_groups(owner_id)
    await callback.message.edit_text(f"🚀 Broadcasting to {len(selected_groups)} groups... Please wait.")
    
    success_count = 0
    failed_count = 0
    
    for chat_id in selected_groups:
        res = await safe_broadcast(callback.bot, owner_id, chat_id, msg)
        if res:
            success_count += 1
        else:
            failed_count += 1
            
    await state.clear()
    await callback.message.answer(
        f"🏁 **Broadcast Finished**\n\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {failed_count}",
        parse_mode="Markdown"
    )