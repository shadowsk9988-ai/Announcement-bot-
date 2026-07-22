import math
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, ADMINISTRATOR
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import group_management_kb
from states import GroupStates

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
async def bot_added_as_admin(event: ChatMemberUpdated):
    owner_id = event.from_user.id
    await db.add_group(owner_id, event.chat.id, event.chat.title)

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> IS_NOT_MEMBER))
async def bot_removed_from_group(event: ChatMemberUpdated):
    # Search which user owned this entry (approximate if multiple users added)
    # For security, we delete only for the user who added it.
    await db.remove_group(event.from_user.id, event.chat.id)

async def render_groups_page(event: Message | CallbackQuery, owner_id: int, page: int = 0, search: str = None):
    all_groups = await db.get_groups(owner_id, search)
    total_count = len(all_groups)
    selected_count = sum(1 for g in all_groups if g[2] == 1)
    
    items_per_page = 10
    total_pages = math.ceil(total_count / items_per_page)
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_groups = all_groups[start_idx:end_idx]
    
    text = (
        f"👥 **Your Groups** ({total_count})\n"
        f"✅ **Selected**: {selected_count}\n"
        f"🔍 Search: {search or 'None'}\n\n"
        f"Page {page + 1} of {max(1, total_pages)}"
    )
    
    kb = group_management_kb(page_groups, page, total_pages, selected_count, total_count)
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("manage_groups:"))
async def list_groups(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await render_groups_page(callback, callback.from_user.id, page)
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_grp:"))
async def toggle_group(callback: CallbackQuery):
    _, chat_id, page = callback.data.split(":")
    await db.toggle_group_selection(callback.from_user.id, int(chat_id))
    await render_groups_page(callback, callback.from_user.id, int(page))
    await callback.answer("Toggled!")

@router.callback_query(F.data.startswith("bulk_select:"))
async def bulk_select(callback: CallbackQuery):
    _, val, page = callback.data.split(":")
    await db.bulk_selection(callback.from_user.id, bool(int(val)))
    await render_groups_page(callback, callback.from_user.id, int(page))
    await callback.answer("Selection updated")

@router.callback_query(F.data == "search_group")
async def start_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GroupStates.searching)
    await callback.message.answer("⌨️ Type the group title to search:")
    await callback.answer()

@router.message(GroupStates.searching)
async def process_search(message: Message, state: FSMContext):
    await state.clear()
    await render_groups_page(message, message.from_user.id, 0, message.text)