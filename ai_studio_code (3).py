from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 New Announcement", callback_data="broadcast_start"))
    builder.row(InlineKeyboardButton(text="👥 My Groups", callback_data="manage_groups:0"))
    builder.row(InlineKeyboardButton(text="📊 Statistics", callback_data="view_stats"))
    builder.row(InlineKeyboardButton(text="ℹ️ Help", callback_data="help_info"))
    builder.row(InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_main"))
    return builder.as_markup()

def group_management_kb(groups, page, total_pages, selected_count, total_count):
    builder = InlineKeyboardBuilder()
    
    for chat_id, title, is_selected in groups:
        status = "✅" if is_selected else "❌"
        builder.row(InlineKeyboardButton(
            text=f"{status} {title}", 
            callback_data=f"toggle_grp:{chat_id}:{page}"
        ))

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"manage_groups:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"manage_groups:{page+1}"))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="➕ Select All", callback_data=f"bulk_select:1:{page}"),
        InlineKeyboardButton(text="➖ Unselect All", callback_data=f"bulk_select:0:{page}")
    )
    builder.row(InlineKeyboardButton(text="🔍 Search Group", callback_data="search_group"))
    builder.row(InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_main"))
    
    return builder.as_markup()

def broadcast_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚀 Confirm & Send", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="back_main")
    )
    return builder.as_markup()