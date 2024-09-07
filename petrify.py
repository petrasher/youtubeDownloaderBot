import os
import re
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
import yt_dlp
import subprocess
import glob

logging.basicConfig(level=logging.INFO)

API_TOKEN = "TOKEN"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

MAX_FILE_SIZE_MB = 48
BYTES_PER_MB = 1024 * 1024

# Создаем блокировку для управления доступом к обработке
processing_lock = asyncio.Lock()

def clean_filename(filename):
    """Очистка имени файла от недопустимых символов и обрезка до допустимой длины"""
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename).strip()
    return filename[:1000]  # Ограничение длины имени файла до 100 символов

@dp.message(Command("start"))
async def start_download(message: types.Message):
    await message.answer("Отправь ссылку на скачивание файла с YouTube:")

@dp.message()
async def process_audio_url(message: types.Message):
    async with processing_lock:
        link = message.text

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',  # Сохранение файлов с именем, соответствующим названию видео
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': False,  # Включаем вывод от yt-dlp для отладки
            'verbose': True, # Включаем более подробный вывод
            'ignoreerrors': True  # Игнорировать ошибки, чтобы продолжать загрузку
        }

        download_message = await message.answer("ОЖИДАЙТЕ! идет загрузка...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                files = glob.glob('*.mp3')
                logging.info(f'Файлы после загрузки: {files}')

                for file_path in files:
                    try:
                        # Очистка имени файла
                        raw_title = os.path.splitext(os.path.basename(file_path))[0]
                        cleaned_title = clean_filename(raw_title)
                        new_file_path = f"{cleaned_title}.mp3"

                        # Переименование файла
                        if file_path != new_file_path:
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path

                        logging.info(f'Обработка файла: {file_path}')
                        file_size_mb = os.path.getsize(file_path) / BYTES_PER_MB
                        logging.info(f'Размер файла: {file_size_mb} MB')

                        if file_size_mb > MAX_FILE_SIZE_MB:
                            num_chunks = int(file_size_mb // MAX_FILE_SIZE_MB) + 1
                            chunk_length_s = float(subprocess.check_output(
                                ['ffprobe', '-v', 'error', '-show_entries',
                                 'format=duration', '-of',
                                 'default=noprint_wrappers=1:nokey=1', file_path]).strip()) / num_chunks
                            logging.info(f'Число кусков: {num_chunks}, длина куска: {chunk_length_s} секунд')

                            for i in range(num_chunks):
                                dividing_message = await message.answer(
                                    "Файл слишком большой, он будет разделен на части. Еще пару минут...")
                                start_time = i * chunk_length_s
                                chunk_name = f"{i + 1}_{cleaned_title}_part.mp3"
                                chunk_path = os.path.abspath(chunk_name)
                                subprocess.call(
                                    ['ffmpeg', '-i', file_path, '-ss', str(start_time), '-t', str(chunk_length_s), '-b:a', '48k',
                                     chunk_path])
                                logging.info(f'Проверка существования части файла: {chunk_path}')
                                if os.path.isfile(chunk_path):
                                    chunk_size = os.path.getsize(chunk_path) / BYTES_PER_MB
                                    logging.info(f'Часть {i + 1}: {chunk_size} MB')
                                    audio_file = FSInputFile(chunk_path)
                                    await bot.send_audio(message.chat.id, audio_file)
                                    os.remove(chunk_path)
                                else:
                                    logging.error(f'Не удалось создать часть файла: {chunk_path}')
                                await bot.delete_message(message.chat.id, dividing_message.message_id)
                        else:
                            audio_file = FSInputFile(file_path)
                            await bot.send_audio(message.chat.id, audio_file)
                            os.remove(file_path)

                    except Exception as e:
                        logging.error(f"Ошибка при обработке файла {file_path}: {e}")
                        await message.answer(f"Произошла ошибка при обработке файла: {e}")
                        os.remove(file_path)

                await bot.delete_message(message.chat.id, message.message_id)
                await bot.delete_message(message.chat.id, download_message.message_id)
                os.remove(file_path)

        except yt_dlp.utils.DownloadError as e:
            await message.answer(f"Произошла ошибка при загрузке: {e}")
            logging.error(f"DownloadError: {e}")

        except Exception as e:
            logging.error(f"Error: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())











