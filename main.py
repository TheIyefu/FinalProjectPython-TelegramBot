import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
import smtplib
from email.message import EmailMessage

# Telegram bot token
TOKEN = '<YOUR_TELEGRAM_BOT_TOKEN>'

# Email settings
EMAIL_USERNAME = '<YOUR_EMAIL_USERNAME>'
EMAIL_PASSWORD = '<YOUR_EMAIL_PASSWORD>'
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_SMTP_PORT = 587

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot handler


class BotHandler:
    def __init__(self, token):
        self.updater = telegram.Updater(token=token, use_context=True)
        self.dispatcher = self.updater.dispatcher

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! How can I assist you?")

    def send_email(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide the email details.")

        # Set the next step handler
        self.dispatcher.register_conversation_next_step_handler(update, [telegram.MessageHandler(telegram.Filters.text, self.handle_email_subject)])

    def handle_email_subject(self, update, context):
        context.user_data['email_subject'] = update.message.text
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please provide the email body.")

        # Set the next step handler
        self.dispatcher.register_conversation_next_step_handler(update, [telegram.MessageHandler(telegram.Filters.text, self.handle_email_body)])

    def handle_email_body(self, update, context):
        email_subject = context.user_data['email_subject']
        email_body = update.message.text

        # Send the email
        try:
            msg = EmailMessage()
            msg.set_content(email_body)
            msg['Subject'] = email_subject
            msg['From'] = EMAIL_USERNAME
            msg['To'] = EMAIL_USERNAME

            with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.send_message(msg)

            context.bot.send_message(chat_id=update.effective_chat.id, text="Email sent successfully!")
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to send the email.")

    def start_bot(self):
        # Register handlers
        self.dispatcher.add_handler(telegram.CommandHandler("start", self.start))
        self.dispatcher.add_handler(telegram.CommandHandler("sendemail", self.send_email))

        # Start the bot
        self.updater.start_polling()
        self.updater.idle()


if __name__ == '__main__':
    bot = BotHandler(TOKEN)
    bot.start_bot()
