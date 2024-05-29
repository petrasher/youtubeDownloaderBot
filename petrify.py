import os
import re
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from pytube import YouTube
import subprocess

logging.basicConfig(level=logging.INFO)

bot = Bot(token="6861882774:AAEBWXTBOy3XilHT4Uix0qT0WPYwS2LgmLQ")
dp = Dispatcher()

MAX_FILE_SIZE_MB = 48
BYTES_PER_MB = 1024 * 1024

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

    file_size_mb = os.path.getsize(file_path) / BYTES_PER_MB
    print(f'Размер файла: {file_size_mb} MB')

    if file_size_mb > MAX_FILE_SIZE_MB:
        num_chunks = int(file_size_mb // MAX_FILE_SIZE_MB) + 1
        chunk_length_s = float(subprocess.check_output(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', file_path]).strip()) / num_chunks
        print(f'Число кусков: {num_chunks}, длина куска: {chunk_length_s} секунд')

        for i in range(num_chunks):
            dividing_message = await message.answer(
                "Файл слишком большой, он будет разделен на части. Еще пару минут...")
            start_time = i * chunk_length_s
            chunk_name = f"{i + 1}_{audio_title}_part.mp3"
            chunk_path = os.path.abspath(chunk_name)
            subprocess.call(
                ['ffmpeg', '-i', file_path, '-ss', str(start_time), '-t', str(chunk_length_s), '-b:a', '48k',
                 chunk_path])
            chunk_size = os.path.getsize(chunk_path) / BYTES_PER_MB
            print(f'Часть {i + 1}: {chunk_size} MB')
            audio_file = FSInputFile(chunk_path)
            await bot.send_audio(message.chat.id, audio_file)
            os.remove(chunk_path)
            await bot.delete_message(message.chat.id, dividing_message.message_id)


    else:
        audio_file = FSInputFile(file_path)
        await bot.send_audio(message.chat.id, audio_file)
        os.remove(file_path)

    await bot.delete_message(message.chat.id, message.message_id)
    await bot.delete_message(message.chat.id, download_message.message_id)
    os.remove(file_path)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
