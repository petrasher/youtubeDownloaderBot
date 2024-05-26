import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from pytube import YouTube

logging.basicConfig(level=logging.INFO)

bot = Bot(token="6861882774:AAEBWXTBOy3XilHT4Uix0qT0WPYwS2LgmLQ")
dp = Dispatcher()


@dp.message(Command("start"))
async def start_download(message: types.Message):
    await message.answer("Отправь ссылку на скачивание файла с YouTube:")


@dp.message()
async def process_audio_url(message: types.Message):
    link = message.text

    audio_info = YouTube(link)
    audio_title = re.sub(r'[/:"*?<>|.,#]', '', audio_info.title)
    file_path = os.path.abspath(f"{audio_title}.mp3")
    download_message = await message.answer("ОЖИДАЙТЕ! идет загрузка файла...")
    print(audio_title)

    audio = audio_info.streams.filter(only_audio=True).first()
    audio.download(filename=f"{audio_title}.mp3")
    print('Загрузка завершена')

    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size > 50:
        await message.answer("Файл слишком большой для отправки (больше 50MB).")
        os.remove(file_path)
        logging.info(f'Файл удален из-за большого размера: {file_path}')
        return

    file_path = os.path.abspath(f"{audio_title}.mp3")
    audio = FSInputFile(file_path)
    await bot.send_audio(message.chat.id, audio)
    await bot.delete_message(message.chat.id, message.message_id)
    await bot.delete_message(message.chat.id, download_message.message_id)
    os.remove(file_path)
    print('Видео удалено')



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
