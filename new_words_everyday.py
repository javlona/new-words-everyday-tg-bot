from decouple import config
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import random
import schedule
import time

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
    chat_id = context.job.context['chat_id']
    num_words = num_words_dict.get(chat_id, default_num_words)

    # Shuffle the list to get random words each time
    random.shuffle(word_list)

    # Select the first N unique words
    selected_words = [word for word in word_list if word not in sent_words_dict.get(chat_id, [])][:num_words]

    # Update the sent words dictionary
    sent_words_dict.setdefault(chat_id, []).extend(selected_words)

    # Trim the dictionary to keep track of only the last 5 sent words
    sent_words_dict[chat_id] = sent_words_dict[chat_id][-num_words:]

    # Join the words into a string
    words_message = " ".join(selected_words)

    # Send the message to the user
    context.bot.send_message(chat_id=chat_id, text=f"Here are your words for today: {words_message}")

# Function to handle the /sendwords command
def send_words_command(update, context):
    # Schedule the send_words job every day at a specific time (in this example, 12:00 PM)
    context.job_queue.run_daily(send_words, time=time(hour=12, minute=0, second=0), context={'chat_id': update.message.chat_id})

    update.message.reply_text("Words will be sent every day at 12:00 PM. Use /start to see this message again.")

# Function to handle the /start command
def start(update, context):
    start_message = "Welcome! This bot sends you 5 random words every day at 12:00 PM. Use /sendwords to start receiving words."
    update.message.reply_text(start_message)

# Function to handle the /setwords command
def set_words(update, context):
    try:
        # Extract the number of words from the user's message
        num_words = int(context.args[0])
        if num_words > 0:
            # Update the number of words for the chat
            num_words_dict[update.message.chat_id] = num_words
            update.message.reply_text(f"Number of words set to {num_words}.")
        else:
            update.message.reply_text("Please enter a positive number.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /setwords <number>")

# Set up the Telegram bot with your token
updater = Updater(config('TELEGRAM_BOT_TOKEN'), use_context=True)

# Get the dispatcher to register handlers
dp = updater.dispatcher

# Register the /sendwords command
dp.add_handler(CommandHandler("sendwords", send_words_command))

# Register the /start command
dp.add_handler(CommandHandler("start", start))

# Register the /setwords command
dp.add_handler(CommandHandler("setwords", set_words, pass_args=True))

# Start the Bot
updater.start_polling()

# Run the bot until you send a signal to stop
updater.idle()
