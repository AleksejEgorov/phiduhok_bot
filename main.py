"""
This is simple bot for memes sharing.
"""
import os
import logging
import asyncio
import sqlite3
import random
import re
import yaml
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
BOT_NAME = 'phiduhok_bot'

os.chdir(os.path.dirname(os.path.realpath(__file__)))
# Import conf
with open('config.yaml', encoding='utf-8') as conf_file:
    conf: dict = yaml.load(conf_file, Loader=yaml.FullLoader)

bot = AsyncTeleBot(conf['telegram_token'])
content_dir = conf['content_dir']
db_path = conf['db_path']
connection = sqlite3.connect(db_path)
cursor = connection.cursor()


async def get_meme_file(meme_caption=''):
    """
    Get a random meme file from the content directory.
    """

    if cursor.execute('SELECT COUNT(*) FROM memes').fetchone()[0] == 0:
        logger.warning('No memes found in %s', content_dir)
        return None
    if meme_caption:
        memes = cursor.execute(
            '''
            SELECT file_path FROM memes
            WHERE caption LIKE ?
            ORDER BY RANDOM()
            ''', ('%' + meme_caption + '%',)
        ).fetchall()
    else:
        memes = cursor.execute('''
            SELECT file_path FROM memes
            ORDER BY RANDOM()
            LIMIT 1
        ''').fetchone()


    logger.info('%s memes found', len(memes))

    if len(memes) > 1:
        meme = random.choice(memes)
    elif len(memes) == 1:
        meme = memes[0]
    else:
        meme = None

    if meme:
        if isinstance(meme, tuple):
            meme = meme[0]
        meme_file = os.path.join(conf['content_dir'],meme)
        logger.info('Selected meme file: %s', meme_file)
        return meme_file
    return None


def gen_markup(buttons):
    '''
    Generates reply keyboard for TG bot
    '''
    req_markup = InlineKeyboardMarkup()
    inline_buttons = []

    for key in list(buttons.keys()):
        inline_buttons.append(InlineKeyboardButton(buttons[key], callback_data=key))

    req_markup.add(*inline_buttons, row_width=len(list(buttons.keys())))
    # s = yaml.dump_all([req_markup])
    # print(s)
    return req_markup


@bot.message_handler(commands=['start'])
async def start_message(message):
    '''
    Process /start command
    '''
    await bot.send_message(
        message.chat.id,
        'Ну?'
    )

@bot.message_handler(regexp="(дай|хочу|покажи|пришли) мем")
async def handle_message(message):
    """
    Handle memes request.
    """
    if message.chat.type == "private" or message.text.startswith('@' + BOT_NAME):
        logger.info('Received message: %s', message.text)
        meme_caption_request = re.sub(
            r'^.+ мем',
            '',
            message.text,
            flags=re.IGNORECASE
        ).strip().lower()

        if (meme_file := await get_meme_file(meme_caption_request)):
            with open(meme_file, 'rb') as file:
                await bot.send_photo(
                    message.chat.id,
                    file
                )
        else:
            await bot.send_message(
                message.chat.id,
                'Mемов не завезли!'
            )

@bot.message_handler(regexp="удоли")
async def handle_delete(message):
    """
    Handle meme delete request.
    """
    if message.chat.type == "private" or message.text.startswith('@' + BOT_NAME):
        logger.info('Received message: %s', message.text)
        meme_caption_request = re.sub(
            r'^.*удоли',
            '',
            message.text,
            flags=re.IGNORECASE
        ).strip().lower()

        if not meme_caption_request:
            await bot.send_message(
                message.chat.id,
                'И шо тут разносить, я тебя спрашиваю?'
            )
            return

        logger.info(
            'Received remove request %s from %s',
            message.from_user.username,
            meme_caption_request
        )

        if (meme_file := await get_meme_file(meme_caption_request)):
            with open(meme_file, 'rb') as file:
                logger.info(
                    'Send remove confirmation for %s to %s',
                    meme_file,
                    message.from_user.username
                )
                await bot.send_photo(
                    message.chat.id,
                    file,
                    reply_markup=gen_markup(
                        {
                            meme_file: 'Удолить',
                            'cb_cancel': 'Не надо'
                        }
                    )
                )
        else:
            await bot.send_message(
                message.chat.id,
                'Mема не завезли!'
            )

@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    """Handles remove callback
    """
    if call.from_user.id not in conf['allowed_ids']:
        await bot.send_message(
            call.chat.id,
            "Ходят тут всякие...",
            parse_mode='markdown'
        )
        return
    if call.data == 'cb_cancel':
        logger.info('Received remove cancel from %s',call.from_user.username)
        await bot.answer_callback_query(call.id, "Оно и к лучшему.")
        await bot.delete_message(call.message.chat.id,call.message.id)
        return

    logger.info('Received remove approve from %s',call.from_user.username)
    cursor.execute('DELETE FROM memes WHERE file_path = ?', (os.path.basename(call.data),))
    connection.commit()
    os.remove(call.data)
    await bot.send_message(
        call.chat.id,
        'И? Лучше стало?'
    )


@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    """
    Handle incoming photos.
    """
    if message.chat.type == "private" or message.caption.startswith('@' + BOT_NAME):
        if message.from_user.id not in conf['allowed_ids']:
            await bot.send_message(
                message.chat.id,
                f"`{message.from_user.id}`"
                + "и ты знаешь, куда с этим идти. "
                + "А от абы кого мемы не берём!",
                parse_mode='markdown'
            )
            return
        logger.info('Received photo from %s', message.from_user.username)
        file_info = await bot.get_file(message.photo[-1].file_id)
        file_path = file_info.file_path
        downloaded_file = await bot.download_file(file_path)

        meme_file_name = f'{message.photo[-1].file_id}.jpg'
        meme_file = os.path.join(content_dir, meme_file_name)
        with open(meme_file, 'wb') as new_file:
            new_file.write(downloaded_file)

        cursor.execute(
            '''
            INSERT INTO memes (file_path, caption)
            VALUES (?, ?)
            ''', (
                meme_file_name,
                message.caption.replace('@' + BOT_NAME, '').strip().lower()
            )
        )
        connection.commit()

        logger.info('Photo saved to %s', meme_file)
        await bot.send_message(
            message.chat.id,
            'Ну!'
        )

@bot.message_handler(
    func=lambda message: True,
    content_types=[
        'audio',
        'voice',
        'video',
        'document',
        'location',
        'contact',
        'sticker'
    ]
)
async def handle_other(message):
    """
    Handle other mediatypes.
    """
    if message.text.startswith('@' + BOT_NAME) or message.chat.type == "private":
        logger.warning('No photo found in message: %s', message.text)
        await bot.send_message(
            message.chat.id,
            'Только картинки принимаем!'
        )


if __name__ == '__main__':
    # create logger
    logging.basicConfig(
        level=str(conf['log_level']).upper(),
        format=conf['log_format']
    )
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memes (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    caption TEXT
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_caption ON memes (caption)')
    connection.commit()

    logger.info('Bot online')
    asyncio.run(bot.infinity_polling())
    connection.close()
