import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from pytube import YouTube

logging.basicConfig(level=logging.INFO)

bot = Bot(token="")
dp = Dispatcher()


@dp.message(Command("start"))
async def start_download(message: types.Message):
    await message.answer("Введите URL видео на YouTube для скачивания:")


@dp.message()
async def process_video_url(message: types.Message):
    link = message.text

    video_info = YouTube(link)
    video_title = re.sub(r'[/:"*?<>|.,#]', '', video_info.title)
    print(video_title)
    video_file_absolute = os.path.abspath(os.path.join(os.path.dirname(__file__), "videos", f"{video_title}.mp4"))
    os.makedirs(os.path.join(os.path.dirname(__file__), "videos"), exist_ok=True)

    video_info.streams.get_highest_resolution().download(output_path='videos')
    print('Загрузка завершена')

    video = FSInputFile(video_file_absolute)
    await bot.send_video(message.chat.id, video=video)
    os.remove(video_file_absolute)
    print('Виде удалено')

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
