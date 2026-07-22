from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Welcome {message.from_user.full_name}!\n\n"
        "This is a professional Announcement Bot. Use the menu below to manage your groups and send broadcasts.",
        reply_markup=main_menu()
    )

@router.callback_query(F.data == "back_main")
@router.callback_query(F.data == "refresh_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 Main Dashboard\n\nManage your groups and announcements securely.",
        reply_markup=main_menu()
    )
    await callback.answer()