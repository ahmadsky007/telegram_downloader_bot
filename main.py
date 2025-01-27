import os
import re
import logging
import threading
import traceback

import yt_dlp
import telebot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "7867125119:AAHW3bnoeXNIYHx0uva9xUxCkFfAeh0MM_E"

if not BOT_TOKEN or BOT_TOKEN.strip() == "":
    raise ValueError("No valid Telegram bot token provided. Please set BOT_TOKEN in the code.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be)(/.*)?",
    re.IGNORECASE
)

INSTAGRAM_REGEX = re.compile(
    r"(https?://)?(www\.)?instagram\.com(/.*)?",
    re.IGNORECASE
)

TIKTOK_REGEX = re.compile(
    r"(https?://)?(www\.)?tiktok\.com(/.*)?",
    re.IGNORECASE
)

TWITTER_REGEX = re.compile(
    r"(https?://)?(www\.)?(twitter\.com|x\.com)(/.*)?",
    re.IGNORECASE
)


def download_media(url: str, resolution: str = None, audio_only: bool = False) -> str:
    """
    Universal download function using yt_dlp for YouTube, Instagram, TikTok, Twitter, etc.
    """
    output_template = "%(title).50B.%(ext)s"

    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "no_warnings": True,
        "restrictfilenames": True,

    }

    if audio_only:
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        if resolution:
            try:
                height = int(resolution.replace("p", ""))
                ydl_opts["format"] = f"bestvideo[height<={height}]+bestaudio/best"
            except ValueError:
                ydl_opts["format"] = "best"
        else:
            ydl_opts["format"] = "best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        if info_dict is None:
            raise ValueError("Failed to retrieve media info.")
        downloaded_filename = ydl.prepare_filename(info_dict)

    return downloaded_filename

def upload_to_third_party(file_path: str) -> str:
    """
    Stub function to upload a file to a third-party service (e.g. Google Drive, Dropbox),
    and return the publicly accessible URL. Implement with your own logic as needed.
    """
    return "https://example.com/your/uploaded/file"


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message):

    welcome_text = (
        "Hello! I'm your Multi-Platform Download Bot.\n"
        "I can download from YouTube, Instagram, TikTok.\n"
        "Use /help to see more options."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['help'])
def send_help(message: telebot.types.Message):

    help_text = (
        "I can download videos from YouTube, Instagram, TikTok, and Twitter.\n\n"
        "Commands:\n"
        "<b>/video &lt;YouTube URL&gt;</b> - Download a YouTube video.\n"
        "<b>/video &lt;resolution&gt; &lt;YouTube URL&gt;</b> - Download a YouTube video with a specific resolution (e.g. 720p).\n"
        "<b>/audio &lt;YouTube URL&gt;</b> - Download audio-only from a YouTube URL.\n\n"
        "<b>/instagram &lt;URL&gt;</b> - Download media from Instagram.\n"
        "<b>/tiktok &lt;URL&gt;</b> - Download media from TikTok.\n"
        "<b>/twitter &lt;URL&gt;</b> - Download media from Twitter (X).\n\n"
        "Or simply send a link directly, and I'll do my best to download."
    )
    bot.reply_to(message, help_text)



@bot.message_handler(commands=['video'])
def handle_video_command(message: telebot.types.Message):

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a YouTube URL after /video.")
            return

        possible_resolution = parts[1]
        video_url = None
        resolution = None


        if len(parts) >= 3:
            resolution = possible_resolution
            video_url = parts[2]
        else:

            video_url = possible_resolution


        if not YOUTUBE_REGEX.match(video_url):
            bot.reply_to(message, "Please provide a valid YouTube URL.")
            return

        download_thread = threading.Thread(
            target=process_download,
            args=(message, video_url, resolution, False)  # audio_only=False
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"Error in /video command: {e}")
        bot.reply_to(message, "An error occurred while processing your request.")


@bot.message_handler(commands=['audio'])
def handle_audio_command(message: telebot.types.Message):

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a YouTube URL after /audio.")
            return

        audio_url = parts[1]
        if not YOUTUBE_REGEX.match(audio_url):
            bot.reply_to(message, "Please provide a valid YouTube URL.")
            return

        download_thread = threading.Thread(
            target=process_download,
            args=(message, audio_url, None, True)
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"Error in /audio command: {e}")
        bot.reply_to(message, "An error occurred while processing your request.")

@bot.message_handler(commands=['instagram'])
def handle_instagram_command(message: telebot.types.Message):

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide an Instagram URL.")
            return

        ig_url = parts[1]
        if not INSTAGRAM_REGEX.match(ig_url):
            bot.reply_to(message, "Please provide a valid Instagram URL.")
            return

        download_thread = threading.Thread(
            target=process_download,
            args=(message, ig_url, None, False)
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"Error in /instagram command: {e}")
        bot.reply_to(message, "An error occurred while processing your request.")

@bot.message_handler(commands=['tiktok'])
def handle_tiktok_command(message: telebot.types.Message):
    """
    /tiktok <URL> to download TikTok video
    """
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a TikTok URL.")
            return

        tk_url = parts[1]
        if not TIKTOK_REGEX.match(tk_url):
            bot.reply_to(message, "Please provide a valid TikTok URL.")
            return

        download_thread = threading.Thread(
            target=process_download,
            args=(message, tk_url, None, False)
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"Error in /tiktok command: {e}")
        bot.reply_to(message, "An error occurred while processing your request.")


@bot.message_handler(commands=['twitter'])
def handle_twitter_command(message: telebot.types.Message):

    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "Please provide a Twitter/X URL.")
            return

        tw_url = parts[1]
        if not TWITTER_REGEX.match(tw_url):
            bot.reply_to(message, "Please provide a valid Twitter/X URL.")
            return

        download_thread = threading.Thread(
            target=process_download,
            args=(message, tw_url, None, False)
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"Error in /twitter command: {e}")
        bot.reply_to(message, "An error occurred while processing your request.")

def process_download(message: telebot.types.Message, url: str, resolution: str = None, audio_only: bool = False):

    try:

        bot.reply_to(message, "Downloading your media, please wait...")

        downloaded_file = download_media(url, resolution=resolution, audio_only=audio_only)
        file_size = os.path.getsize(downloaded_file)
        two_gb_in_bytes = 2 * 1024 * 1024 * 1024

        if file_size > two_gb_in_bytes:
            bot.send_message(message.chat.id, "File is larger than 2GB. Uploading to external service...")
            external_link = upload_to_third_party(downloaded_file)
            bot.send_message(message.chat.id,
                             f"Your file is too large for Telegram. Download it here:\n{external_link}")
        else:
            with open(downloaded_file, 'rb') as media_file:
                if audio_only:

                    bot.send_audio(message.chat.id, media_file)
                else:

                    bot.send_video(message.chat.id, media_file)

    except Exception as e:
        logger.error(f"Error downloading or sending media: {traceback.format_exc()}")
        bot.reply_to(message, f"Failed to download media: {str(e)}")
    finally:

        if 'downloaded_file' in locals() and os.path.exists(downloaded_file):
            os.remove(downloaded_file)


@bot.message_handler(func=lambda msg: True, content_types=['text'])
def handle_text_message(message: telebot.types.Message):

    text = message.text.strip()


    if YOUTUBE_REGEX.match(text):

        download_thread = threading.Thread(
            target=process_download,
            args=(message, text, None, False)
        )
        download_thread.start()
    elif INSTAGRAM_REGEX.match(text):
        download_thread = threading.Thread(
            target=process_download,
            args=(message, text, None, False)
        )
        download_thread.start()
    elif TIKTOK_REGEX.match(text):
        download_thread = threading.Thread(
            target=process_download,
            args=(message, text, None, False)
        )
        download_thread.start()
    elif TWITTER_REGEX.match(text):
        download_thread = threading.Thread(
            target=process_download,
            args=(message, text, None, False)
        )
        download_thread.start()
    else:
        bot.reply_to(message, "Send a YouTube, Instagram, TikTok, or Twitter link, or use /help for commands.")

def main():
    logger.info("Starting Telegram bot...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")


if __name__ == "__main__":
    main()
