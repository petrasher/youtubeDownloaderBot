try:
    video_info = YouTube(video_url)
    video_title = re.sub(r'[/:"*?<>|]', '_', video_info.title)
    video_file_absolute = os.path.abspath(os.path.join(os.path.dirname(__file__), "videos",
                                                       f"{video_title}.mp4"))

    os.makedirs(os.path.join(os.path.dirname(__file__), "videos"), exist_ok=True)

    print("Скачивание видео...")
    await asyncio.to_thread(video_info.streams.get_highest_resolution().download,
                            output_path="videos")
    print("Скачивание завершено.")

    print("Отправка видео...")
    with open(video_file_absolute, 'rb') as video_opened:
        await bot.send_video(message.chat.id, video=video_opened)
    print("Отправка завершена.")

    await message.answer("Видео успешно отправлено!")

except Exception as e:
    print("Ошибка при скачивании и отправке видео:", e)
    await message.answer("Ошибка при скачивании и отправке видео. Пожалуйста, убедитесь, что URL корректен.")