from decouple import config
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from datetime import time
import random
import requests
import json

# File path to store user information
user_info_file_path = "user_info.json"

# Define conversation states
SET_WORDS = 0

# Function to read words from a text file
def read_words_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

# Your list of words from the text file
word_list_file_path = "word_list.txt"
word_list = read_words_from_file(word_list_file_path)

# Dictionary to store sent words for each chat
sent_words_dict = {}

# Dictionary to store the number of words to send for each chat
num_words_dict = {}

# Default number of words
default_num_words = 5

# Function to send words
def send_words(context):
    chat_id = context['chat_id']
    num_words = num_words_dict.get(chat_id, default_num_words)

    # Shuffle the list to get random words each time
    random.shuffle(word_list)

    # Select the first N unique words
    selected_words = [word for word in word_list if word not in sent_words_dict.get(chat_id, [])][:num_words]

    # Update the sent words dictionary
    sent_words_dict.setdefault(chat_id, []).extend(selected_words)

    # Trim the dictionary to keep track of only the last 5 sent words
    sent_words_dict[chat_id] = sent_words_dict[chat_id][-num_words:]

    # Create a string with each word on a new line
    words_message = "\n".join(selected_words)

    # Send the message to the user using the Telegram Bot API
    bot_token = config('TELEGRAM_BOT_TOKEN')
    bot_chatID = chat_id  # You may need to adjust this depending on how you obtain the chat ID

    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chatID}&parse_mode=Markdown&text={words_message}'
    requests.get(send_text)

# Function to handle the /sendnow command
def send_now_command(update, context):
    # Create a new context manually
    job_context = {'chat_id': update.message.chat_id}
    send_words(job_context)

# Function to handle the /help command
def help_command(update, context):
    help_message = (
        "Here are the available commands:\n"
        "/start - Start receiving 5 random words every day at 12:00 PM.\n"
        "/sendwords - Schedule the delivery of random words at 12:00 PM.\n"
        "/setwords <number> - Set the number of words to receive each day.\n"
        "/sendnow - Get the words now.\n"
        "/help - Display this help message."
    )
    update.message.reply_text(help_message)

# Function to handle the /start command
def start(update, context):
    user = update.message.from_user
    user_id = user.id
    user_first_name = user.first_name
    user_last_name = user.last_name
    user_username = user.username

    start_message = (
        "Welcome! This bot sends you 5 random words every day at 12:00 PM. Use /sendwords to start receiving words.\n"
        "Here are the available commands:\n"
        "/start - Start receiving 5 random words every day at 12:00 PM.\n"
        "/sendwords - Schedule the delivery of random words at 12:00 PM.\n"
        "/setwords <number> - Set the number of words to receive each day.\n"
        "/sendnow - Get the words now.\n"
        "/help - Display this help message."
    )

    # Save user information to the file
    save_user_info(user_id, user_first_name, user_last_name, user_username)

    # Create a custom keyboard with menu buttons
    menu_buttons = [
        [KeyboardButton("/sendwords"), KeyboardButton("/setwords")],
        [KeyboardButton("/sendnow"), KeyboardButton("/help")]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)

    # Send the start message with the menu
    update.message.reply_text(start_message, reply_markup=reply_markup)

# Function to save user information
def save_user_info(user_id, first_name, last_name, username):
    # Load existing user information from the file
    user_info = load_user_info()

    # Add or update user information
    user_info[user_id] = {
        "first_name": first_name,
        "last_name": last_name,
        "username": username
    }

    # Save the updated user information back to the file
    with open(user_info_file_path, 'w') as file:
        json.dump(user_info, file)

def load_user_info():
    try:
        # Load user information from the file
        with open(user_info_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, return an empty dictionary
        return {}

# ... (continued from Part 1)

# Function to handle the /sendwords command
def send_words_command(update, context):
    chat_id = update.message.chat_id
    num_words = num_words_dict.get(chat_id, default_num_words)

    # Create a message to inform the user about receiving words
    info_message = f"You will receive {num_words} words every day at 12:00 PM."

    # Send the information message
    context.bot.send_message(chat_id=chat_id, text=info_message)

    # Schedule the send_words job every day at 12:00 PM
    context.job_queue.run_daily(send_words, time=time(hour=12, minute=0, second=0), context={'chat_id': chat_id})

    # # Create a custom keyboard with menu buttons
    # menu_buttons = [
    #     [KeyboardButton("/sendwords"), KeyboardButton("/setwords")],
    #     [KeyboardButton("/help")]
    # ]
    # reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True, one_time_keyboard=True)

    # # Send the information message along with the menu
    # update.message.reply_text(info_message, reply_markup=reply_markup)

# Create a conversation state for setting the number of words
SET_WORDS = 0

# Function to handle the /setwords command
def set_words(update, context):
    update.message.reply_text("Enter the number of words you want to receive every day:")

    return SET_WORDS

# Function to handle the user's input for setting the number of words
def set_words_input(update, context):
    try:
        num_words = int(update.message.text)
        if num_words > 0:
            num_words_dict[update.message.chat_id] = num_words
            update.message.reply_text(f"Number of words set to {num_words}.")
        else:
            update.message.reply_text("Please enter a positive number.")
        
    except ValueError:
        update.message.reply_text("Invalid input. Please enter a valid number.")
        
    # End the conversation and remove the custom keyboard
    return ConversationHandler.END

# Create a ConversationHandler for the /setwords command
set_words_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("setwords", set_words)],
    states={
        SET_WORDS: [MessageHandler(Filters.text & ~Filters.command, set_words_input)]
    },
    fallbacks=[],
    per_user=False
)

# Set up the Telegram bot with your token
updater = Updater(config('TELEGRAM_BOT_TOKEN'), use_context=True)

# Get the dispatcher to register handlers
dp = updater.dispatcher

# Register the /sendwords command
dp.add_handler(CommandHandler("sendwords", send_words_command))

# Register the /start command
dp.add_handler(CommandHandler("start", start))

# Register the /setwords command using the ConversationHandler
dp.add_handler(set_words_conv_handler)

# Register the /sendnow command
dp.add_handler(CommandHandler("sendnow", send_now_command))

# Register the /help command
dp.add_handler(CommandHandler("help", help_command))

# Start the Bot
updater.start_polling()

# Run the bot until you send a signal to stop
updater.idle()
