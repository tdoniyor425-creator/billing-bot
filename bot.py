import os
import glob
import logging
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Tokeningiz
TOKEN = "8836945702:AAGfW5DOIWCFo2iBuDm5nMnUImRIoxz17Rw" 

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Papkadagi yagona Excel faylni topish
def get_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Papkadan har qanday .xlsx yoki .xls faylni qidiramiz
    files = glob.glob(os.path.join(script_dir, "*.xlsx")) + glob.glob(os.path.join(script_dir, "*.xls"))
    
    if not files:
        print("❌ XATOLIK: Papkada Excel fayl topilmadi!")
        return None
    
    # Birinchi topilgan Excel faylni ochamiz
    file_path = files[0]
    print(f"📂 Topilgan Excel fayl: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return None

# Bot bosqichlari (FSM)
class BotStates(StatesGroup):
    mahalla = State()
    uy = State()
    xonadon = State()

# /start buyrug'i
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    df = get_data()
    
    if df is None:
        await message.answer("⚠️ Xatolik: Excel fayl topilmadi!")
        return

    try:
        mahallas = df["Mahalla"].dropna().unique()
    except KeyError:
        await message.answer("⚠️ Xatolik: Excel faylda 'Mahalla' ustuni topilmadi!")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=str(m), callback_data=f"mah_{m}")] for m in mahallas]
    )
    await message.answer("🏠 Iltimos, mahallani tanlang:", reply_markup=keyboard)
    await state.set_state(BotStates.mahalla)

# Mahalla tanlanganda
@dp.callback_query(F.data.startswith("mah_"))
async def choose_mahalla(call: types.CallbackQuery, state: FSMContext):
    mahalla = call.data.split("_", 1)[1]
    await state.update_data(mahalla=mahalla)
    
    df = get_data()
    uys = df[df["Mahalla"] == mahalla]["Uy"].dropna().unique()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=str(u), callback_data=f"uy_{u}")] for u in uys]
    )
    await call.message.edit_text(f"Mahalla: **{mahalla}**\n\n🛣 Uyni tanlang:", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BotStates.uy)
    await call.answer()

# Uyni tanlanganda
@dp.callback_query(F.data.startswith("uy_"))
async def choose_uy(call: types.CallbackQuery, state: FSMContext):
    uy = call.data.split("_", 1)[1]
    await state.update_data(uy=uy)
    data = await state.get_data()
    
    df = get_data()
    xonadons = df[(df["Mahalla"] == data["mahalla"]) & (df["Uy"].astype(str) == str(uy))]["Xonadon"].dropna().unique()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=str(x), callback_data=f"xon_{x}")] for x in xonadons]
    )
    await call.message.edit_text(f"Uy: **{uy}**\n\n🚪 Xonadonni tanlang:", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BotStates.xonadon)
    await call.answer()

# Xonadon tanlanganda va hisob raqamni chiqarish
@dp.callback_query(F.data.startswith("xon_"))
async def choose_xonadon(call: types.CallbackQuery, state: FSMContext):
    xonadon = call.data.split("_", 1)[1]
    data = await state.get_data()
    
    df = get_data()
    row = df[
        (df["Mahalla"] == data["mahalla"]) & 
        (df["Uy"].astype(str) == str(data["uy"])) & 
        (df["Xonadon"].astype(str) == str(xonadon))
    ]
    
    if not row.empty:
        hisob = row.iloc[0]["Hisob raqam"]
        text = (
            f"✅ **Manzil topildi:**\n"
            f"• Mahalla: {data['mahalla']}\n"
            f"• Uy: {data['uy']}\n"
            f"• Xonadon: {xonadon}\n\n"
            f"💳 **Hisob raqam:** `{hisob}`"
        )
    else:
        text = "Kechirasiz, bu manzil bo'yicha ma'lumot topilmadi."
        
    await call.message.edit_text(text, parse_mode="Markdown")
    await state.clear()
    await call.answer()

if __name__ == "__main__":
    import asyncio
    print("Bot ishga tushdi...")
    asyncio.run(dp.start_polling(bot))
    # Render port talab qilgani uchun kichik veb-server
from aiohttp import web
import os

async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

async def web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    if __name__ == "__main__":
    import asyncio
    print("Bot ishga tushdi...")
    
    loop = asyncio.get_event_loop()
    loop.create_task(web_server())
    loop.run_until_complete(dp.start_polling(bot))
