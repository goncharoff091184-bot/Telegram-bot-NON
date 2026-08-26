import asyncio
import os
import json
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей (временно, в памяти)
# Потом заменим на базу данных
user_data = {}

# Главное меню
def get_main_menu():
    buttons = [
        [InlineKeyboardButton(text="📸 Загрузить фото", callback_data="upload")],
        [InlineKeyboardButton(text="📋 Мои фото", callback_data="my_photos")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Команда /start
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"photos": [], "settings": {}}
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я — бот для анализа фотографий и их метаданных.\n"
        "📸 Отправляй мне фото, а я:\n"
        "• Извлеку все EXIF-данные\n"
        "• Покажу дату, место, камеру и настройки\n"
        "• Соберу статистику по всем твоим фото\n\n"
        "Выбери действие:",
        reply_markup=get_main_menu()
    )

# Обработка кнопок меню
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    await callback.answer()
    
    if callback.data == "upload":
        await callback.message.edit_text(
            "📸 **Загрузи фото**\n\n"
            "Просто отправь мне любое фото.\n"
            "Я извлеку из него все метаданные:\n"
            "• 📅 Дата и время съёмки\n"
            "• 📍 GPS-координаты (если есть)\n"
            "• 📷 Модель камеры\n"
            "• ⚙️ Настройки: ISO, диафрагма, выдержка\n"
            "• 🖼️ Размеры и разрешение",
            reply_markup=get_main_menu()
        )
    
    elif callback.data == "my_photos":
        user_id = str(callback.from_user.id)
        photos = user_data.get(user_id, {}).get("photos", [])
        
        if not photos:
            await callback.message.edit_text(
                "📋 **У тебя пока нет загруженных фото**\n\n"
                "Нажми «Загрузить фото» и отправь мне первую фотографию!",
                reply_markup=get_main_menu()
            )
        else:
            text = f"📋 **Твои фото ({len(photos)} шт.)**\n\n"
            for i, photo in enumerate(photos[-5:], 1):  # показываем последние 5
                text += f"{i}. {photo.get('filename', 'Без имени')}\n"
                text += f"   📅 {photo.get('date', 'Нет даты')}\n"
                text += f"   📷 {photo.get('camera', 'Неизвестно')}\n\n"
            
            if len(photos) > 5:
                text += f"… и ещё {len(photos) - 5} фото\n\n"
            
            text += "Скоро добавлю просмотр каждого фото с деталями!"
            
            await callback.message.edit_text(
                text,
                reply_markup=get_main_menu()
            )
    
    elif callback.data == "stats":
        await callback.message.edit_text(
            "📊 **Статистика по фото**\n\n"
            "Здесь будет:\n"
            "• Всего фото: 0\n"
            "• Самая популярная камера\n"
            "• Диапазон дат съёмки\n"
            "• Карта с геолокациями\n"
            "• Средние настройки (ISO, выдержка)\n\n"
            "Скоро добавлю!",
            reply_markup=get_main_menu()
        )
    
    elif callback.data == "settings":
        await callback.message.edit_text(
            "⚙️ **Настройки**\n\n"
            "Выбери, что настроить:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌍 Единицы измерения", callback_data="settings_units")],
                [InlineKeyboardButton(text="📊 Формат отчётов", callback_data="settings_report")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ])
        )
    
    elif callback.data == "back_to_main":
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
    
    elif callback.data == "settings_units":
        await callback.message.edit_text(
            "🌍 **Единицы измерения**\n\n"
            "Выбери систему:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📏 Метрическая (км, м)", callback_data="units_metric")],
                [InlineKeyboardButton(text="📏 Имперская (мили, футы)", callback_data="units_imperial")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="settings")]
            ])
        )
    
    elif callback.data in ["units_metric", "units_imperial"]:
        await callback.message.edit_text(
            "✅ Настройки сохранены!",
            reply_markup=get_main_menu()
        )
    
    elif callback.data == "settings_report":
        await callback.message.edit_text(
            "📊 **Формат отчётов**\n\n"
            "Выбери формат:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📄 Текстовый", callback_data="report_text")],
                [InlineKeyboardButton(text="📊 Графики", callback_data="report_charts")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="settings")]
            ])
        )
    
    elif callback.data in ["report_text", "report_charts"]:
        await callback.message.edit_text(
            "✅ Настройки сохранены!",
            reply_markup=get_main_menu()
        )

# Обработка загруженных фото
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    user_id = str(message.from_user.id)
    
    # Получаем информацию о фото
    photo = message.photo[-1]  # самое большое разрешение
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path
    
    # Скачиваем фото
    downloaded_file = await bot.download_file(file_path)
    
    # Сохраняем временно
    temp_path = f"temp_{user_id}_{datetime.now().timestamp()}.jpg"
    with open(temp_path, "wb") as f:
        f.write(downloaded_file.getvalue())
    
    # Анализируем метаданные
    metadata = extract_metadata(temp_path)
    
    # Сохраняем в историю пользователя
    if user_id not in user_data:
        user_data[user_id] = {"photos": []}
    
    user_data[user_id]["photos"].append({
        "file_id": photo.file_id,
        "filename": f"photo_{len(user_data[user_id]['photos']) + 1}.jpg",
        "date": metadata.get("date", "Нет данных"),
        "camera": metadata.get("camera", "Неизвестно"),
        "metadata": metadata
    })
    
    # Формируем ответ
    response = "📸 **Фото получено!**\n\n"
    response += "**📋 Метаданные:**\n"
    
    if metadata:
        for key, value in metadata.items():
            if value and value != "Нет данных" and value != "Неизвестно":
                emoji = get_emoji_for_key(key)
                response += f"{emoji} **{key}:** {value}\n"
    else:
        response += "❌ Метаданные не найдены (или фото без EXIF)\n"
    
    response += "\nНажми «Мои фото», чтобы увидеть все загруженные снимки."
    
    await message.answer(response, reply_markup=get_main_menu())
    
    # Удаляем временный файл
    os.remove(temp_path)

def extract_metadata(image_path):
    """Извлекает EXIF-данные из фото"""
    metadata = {}
    
    try:
        image = Image.open(image_path)
        exifdata = image.getexif()
        
        if not exifdata:
            return metadata
        
        for tag_id, value in exifdata.items():
            tag = TAGS.get(tag_id, tag_id)
            
            if tag == "Make":
                metadata["Производитель"] = value
            elif tag == "Model":
                metadata["Камера"] = value
            elif tag == "DateTime":
                metadata["Дата"] = value
            elif tag == "ISOSpeedRatings":
                metadata["ISO"] = value
            elif tag == "FNumber":
                metadata["Диафрагма"] = f"f/{value}"
            elif tag == "ExposureTime":
                metadata["Выдержка"] = str(value)
            elif tag == "FocalLength":
                metadata["Фокусное"] = f"{value} мм"
            elif tag == "GPSInfo":
                gps_data = extract_gps(exifdata)
                if gps_data:
                    metadata["GPS"] = gps_data
        
        # Добавляем размеры
        metadata["Размер"] = f"{image.width}x{image.height}"
        
    except Exception as e:
        print(f"Ошибка при извлечении EXIF: {e}")
    
    return metadata

def extract_gps(exifdata):
    """Извлекает GPS-координаты"""
    try:
        gps_info = {}
        for key in exifdata:
            if key in GPSTAGS:
                gps_info[GPSTAGS[key]] = exifdata[key]
        
        if not gps_info:
            return None
        
        # Преобразуем координаты
        lat = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')
        
        if lat and lon:
            lat_val = convert_to_degrees(lat)
            if lat_ref != 'N':
                lat_val = -lat_val
            
            lon_val = convert_to_degrees(lon)
            if lon_ref != 'E':
                lon_val = -lon_val
            
            return f"{lat_val:.6f}, {lon_val:.6f}"
    except:
        pass
    
    return None

def convert_to_degrees(value):
    """Конвертирует GPS-координаты из формата (градусы, минуты, секунды) в градусы"""
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_emoji_for_key(key):
    """Возвращает эмодзи для типа метаданных"""
    emojis = {
        "Производитель": "🏭",
        "Камера": "📷",
        "Дата": "📅",
        "ISO": "🔆",
        "Диафрагма": "⭕",
        "Выдержка": "⏱️",
        "Фокусное": "🔭",
        "Размер": "📐",
        "GPS": "📍"
    }
    return emojis.get(key, "•")

async def main():
    print("🤖 Бот для анализа фотографий запущен!")
    print("📸 Отправляй фото для анализа метаданных")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
