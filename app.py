import os
import re
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackQueryHandler, ContextTypes, CallbackContext
from upload import upload_to_drive, search_xspf_files, download_from_drive, search_files

# Constants for configuration
TELEGRAM_TOKEN = '7132282392:AAHWSjExwrcyshy7WgYXqYJOYvv-yMJLFIU'
FOLDER_ID = '13KFeXalCmIykzFUBWVaXAifweejjhVnk'
CREDENTIALS_FILE = 'apikeys.json'

# Allowed video file extensions
video_extensions = re.compile(r'\.(mkv|mp4|avi|mpeg|wmv|asf|mov|flv|ogg|webm)$', re.IGNORECASE)

# Function to create XSPF file
def create_xspf(file_name):
    encoded_file_name = quote(file_name)
    xspf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">
    <title>Playlist</title>
    <trackList>
        <track>
            <location>https://www.1drive.me/api/raw/?path=/OneDriveXbot/{encoded_file_name}</location>
            <title>{file_name}</title>
            <extension application="http://www.videolan.org/vlc/playlist/0">
                <vlc:id>0</vlc:id>
            </extension>
        </track>
    </trackList>
    <extension application="http://www.videolan.org/vlc/playlist/0">
        <vlc:item tid="0"/>
    </extension>
</playlist>'''

    xspf_file_name = f"{os.path.splitext(file_name)[0]}.xspf"
    with open(xspf_file_name, 'w', encoding='utf-8') as f:
        f.write(xspf_content)
    return xspf_file_name

# Handler for the command messages
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    command_name = message.text.split('@')[0]

    if message.reply_to_message:
        quoted_message = message.reply_to_message

        file_id, file_name = None, None

        if quoted_message.video:
            file_id = quoted_message.video.file_id
            file_name = quoted_message.video.file_name or f'{file_id}.mp4'
        elif quoted_message.document:
            file_id = quoted_message.document.file_id
            file_name = quoted_message.document.file_name

        if file_id and file_name and video_extensions.search(file_name):
            await process_video_file(update, context, file_name)
        else:
            if command_name == '/xspf':
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Quoted message does not contain a valid video file"
                )
    else:
        if command_name == '/xspf':
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No quoted message found"
            )

async def process_video_file(update, context, file_name):
    xspf_files = search_xspf_files(FOLDER_ID, CREDENTIALS_FILE)
    xspf_file_name = os.path.splitext(file_name)[0] + ".xspf"
    caption = "Open this file to play the movie in VLC.\n(Works only after the upload is completed by Ragannan)"
    user_id = update.message.from_user.id
    
    if xspf_file_name not in xspf_files:
        xspf_file_name = create_xspf(file_name)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption=caption
            )
            await context.bot.send_document(
                chat_id="-4153377397",
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name)
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"XSPF file is in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
                #parse_mode='Markdown'
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(xspf_file_name, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption=caption,
                reply_to_message_id=update.message.message_id
            )
        
        file_path = os.path.abspath(xspf_file_name)
        upload_to_drive(file_path, FOLDER_ID, CREDENTIALS_FILE)
        os.remove(xspf_file_name)
    else:
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=user_id,
                text="XSPF file already exists for this video."
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"XSPF file is in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
                #parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="XSPF file already exists for this video."
            )
        file_temp = download_from_drive(xspf_file_name, FOLDER_ID, CREDENTIALS_FILE)
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_document(
                chat_id=user_id,
                document=open(file_temp, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption="Ready to play!--->"
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(file_temp, 'rb'),
                filename=os.path.basename(xspf_file_name),
                caption="Ready to play!--->",
                reply_to_message_id=update.message.message_id
            )
        os.remove(file_temp)

async def nokate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    xspf_files = search_xspf_files(FOLDER_ID, CREDENTIALS_FILE)
    if xspf_files:
        keyboard_buttons = []
        for file_index, file_name in enumerate(xspf_files):
            button = InlineKeyboardButton(text=file_name, callback_data=f"select:{file_index + 1}")
            keyboard_buttons.append([button])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text='Click on the below file to download:',
                reply_markup=keyboard
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Files listed in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
                #parse_mode='Markdown'
            )
        else:
            await update.message.reply_text('Click on the below file to download:', reply_markup=keyboard)

# Handler for callback queries from inline buttons
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    callback_data = query.data.split(':')
    action = callback_data[0]
    if action == 'select':
        if len(callback_data) == 2:
            file_index = int(callback_data[1]) - 1  
            xspf_files = search_xspf_files(FOLDER_ID, CREDENTIALS_FILE)
            if xspf_files and 0 <= file_index < len(xspf_files):
                selected_file_name = xspf_files[file_index]
                file_name = os.path.splitext(selected_file_name)[0] + ".xspf"
                file_info = download_from_drive(file_name, FOLDER_ID, CREDENTIALS_FILE)
                if file_info:
                    if query.message.chat.type in ['group', 'supergroup']:
                        await context.bot.send_document(
                            chat_id=query.from_user.id,
                            document=open(file_info, 'rb'),
                            filename=file_name
                        )
                    else:
                        await context.bot.send_document(
                            chat_id=query.message.chat.id,
                            document=open(file_info, 'rb'),
                            filename=file_name,
                            reply_to_message_id=query.message.message_id
                        )
                    os.remove(file_info)
                    await query.message.delete()
        else:
            await query.message.reply_text('Invalid selection.')
    elif action == 'download':
        if len(callback_data) == 2:
            global file_name2
            file_name = os.path.splitext(file_name2)[0] + ".xspf"
            file_info = download_from_drive(file_name, FOLDER_ID, CREDENTIALS_FILE)
            if file_info:
                if query.message.chat.type in ['group', 'supergroup']:
                    await context.bot.send_document(
                        chat_id=query.from_user.id,
                        document=open(file_info, 'rb'),
                        filename=file_name
                    )
                else:
                    await context.bot.send_document(
                        chat_id=query.message.chat.id,
                        document=open(file_info, 'rb'),
                        filename=file_name,
                        reply_to_message_id=query.message.message_id
                    )
                os.remove(file_info)
                await query.message.delete()
            else:
                await query.message.reply_text('Failed to download the file.')
        else:
            await query.message.reply_text('Invalid selection.')
    elif action == 'cancel':
        await query.message.delete()

# Handler for /ping command
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('pong')

# Handler for /search command
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text('Please provide a search term.')
        return
    
    results = search_files(FOLDER_ID, query, CREDENTIALS_FILE)
    if results:
        keyboard_buttons = []
        for file_index, file in enumerate(results):
            file_name = file["name"]
            button = InlineKeyboardButton(text=file_name, callback_data=f"select:{file_index + 1}")
            keyboard_buttons.append([button])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        if update.effective_chat.type in ['group', 'supergroup']:
            await context.bot.send_message(
                chat_id=update.message.from_user.id,
                text='Click on the below file to download:',
                reply_markup=keyboard
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Files listed in bots PM @naabi7_bot",
                reply_to_message_id=update.message.message_id
                #parse_mode='Markdown'
            )
        else:
            await update.message.reply_text('Click on the below file to download:', reply_markup=keyboard)
    else:
        # if update.effective_chat.type in ['group', 'supergroup']:
        #     await context.bot.send_message(
        #         chat_id=update.message.from_user.id,
        #         text='No files found.'
        #     )
        # else:
        await update.message.reply_text('No files found.')

# Handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hi! Send a video file in the group and\n'
        'I will generate an XSPF file for it.\n'
        'The file needs to be uploaded by the Ragannan <BOT>.\n'
        'By using the /m commands of Ragannan.'
        'This .xspf file can be used to watch the movie that has been uploaded.\n'
        'Use /nokate to check for .xspf files that are ready to stream.\n'
        'Use /find to searcg for .xspf files that are already uploaded.\n'
        'Ex:  /find atlas -->\n'
        '-->will show the movies with name of atlas in my pm.\n'
        'The archive group for the xspf files are at https://t.me/+IvRoFcdYRW5iZWJl ..$'
    )

# Main function to run the bot
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    command_filters = filters.Regex(r'^/(m|mirror|mirror@cowardppbot|xspf|xspf@naabi7_bot)$')

    application.add_handler(MessageHandler(command_filters, handle_command))
    application.add_handler(CommandHandler('ping', ping))
    application.add_handler(CommandHandler('nokate', nokate))
    application.add_handler(CommandHandler('help', start))
    application.add_handler(CommandHandler('find', search))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()
