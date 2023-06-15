import os
import logging
import telebot
import smtplib
import ssl
from dotenv import load_dotenv
from email.message import EmailMessage
from telebot import types

load_dotenv()

# Telegram bot token
TOKEN = os.getenv('TOKEN')

# Email settings
EMAIL_USERNAME = 'favyiyefu@gmail.com'
EMAIL_PASSWORD = os.getenv('PASSWORD')
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_SMTP_PORT = 465

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a bot instance
bot = telebot.TeleBot(TOKEN)


class BaseHandler:
    def __init__(self, bot):
        self.bot = bot

    def send_email(self, message):
        raise NotImplementedError("send_email method must be implemented in derived classes.")

    def send_message(self, chat_id, message, reply_markup=None):
        self.bot.send_message(chat_id, message, reply_markup=reply_markup)


# Telegram bot handler
class BotHandler(BaseHandler):
    def send_email(self, message):
        chat_id = message.chat.id
        self.send_message(chat_id, "Please provide the recipient's email addresses, separated by commas."
                                   "\nПожалуйста, укажите адреса электронной почты получателей, "
                                   "разделив их запятыми.")

        # Register the next step handler
        self.bot.register_next_step_handler(message, self.handle_email_recipients)

    def handle_email_recipients(self, message):
        chat_id = message.chat.id
        recipients = message.text.split(',')
        recipients = [email.strip() for email in recipients]
        print(recipients)
        self.send_message(chat_id, "Please provide the email subject."
                                   "\nПожалуйста, укажите тему электронного письма.")

        # Register the next step handler
        self.bot.register_next_step_handler(message, self.handle_email_subject, recipients)

    def handle_email_subject(self, message, recipients):
        chat_id = message.chat.id
        email_subject = message.text
        print(email_subject)
        self.send_message(chat_id, "Please provide the email body."
                                   "\nПожалуйста, укажите текст электронного письма.")

        # Register the next step handler
        self.bot.register_next_step_handler(message, self.handle_email_body, recipients, email_subject)

    def handle_email_body(self, message, recipients, email_subject):
        chat_id = message.chat.id
        email_body = message.text
        print(email_body)

        # Create a pop-up menu with two options
        keyboard = self.create_menu(["Yes", "No"], one_time_keyboard=True)
        self.send_message(chat_id, "Do you want to upload an image?"
                                   "\nВы хотите загрузить изображение?", reply_markup=keyboard)

        # Register the next step handler
        self.bot.register_next_step_handler(message, self.handle_upload_choice, recipients, email_subject, email_body)

    def handle_upload_choice(self, message, recipients, email_subject, email_body):
        chat_id = message.chat.id

        if message.text.lower() == 'yes' or message.text.lower() == 'да':
            self.send_message(chat_id, "Please upload the image(s). Send 'done' when finished."
                                       "(Send one image at a time)"
                                       "\nПожалуйста, загрузите изображение (изображения). Отправьте 'done', "
                                       "когда закончите. (Отправляйте по одному изображению за раз)")
            # Register the next step handler
            self.bot.register_next_step_handler(message, self.handle_uploaded_images, recipients, email_subject,
                                                email_body, [])
        else:
            self.send_email_without_images(chat_id, recipients, email_subject, email_body)

    def handle_uploaded_images(self, message, recipients, email_subject, email_body, images):
        chat_id = message.chat.id

        if message.photo:
            # ...
            self.send_message(chat_id, "Image uploaded successfully. You can upload more images or send 'done'."
                                       "\nИзображение успешно загружено. Вы можете загрузить больше изображений или "
                                       "отправить 'done'.")

            # Register the next step handler recursively
            self.bot.register_next_step_handler(message, self.handle_uploaded_images, recipients, email_subject,
                                                email_body, images)
        elif message.text.lower() == 'done' or message.text.lower() == 'готово':
            self.send_email_with_images(chat_id, recipients, email_subject, email_body, images)
        else:
            self.send_message(chat_id, "Invalid input. Please upload an image or send 'done'."
                                       "\nНеверный ввод. Пожалуйста, загрузите изображение или отправьте 'done'.")

    def create_menu(self, menu_options, one_time_keyboard=False):
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=one_time_keyboard)
        keyboard.add(*[types.KeyboardButton(option) for option in menu_options])
        return keyboard

    def send_email_without_images(self, chat_id, recipients, email_subject, email_body):
        try:
            msg = EmailMessage()
            msg['From'] = EMAIL_USERNAME
            msg['To'] = recipients
            msg['Subject'] = email_subject
            msg.set_content(email_body)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, context=context) as smtp:
                smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                smtp.send_message(msg)

            self.send_message(chat_id, "Email sent successfully!"
                                       "\nЭлектронное письмо успешно отправлено!")
        except Exception as e:
            logger.error(f"Failed to send the email: {str(e)}"
                         f"\nНе удалось отправить электронное письмо: {str(e)}")
            self.send_message(chat_id, "Failed to send the email. Please check the logs for more information."
                                       "\nНе удалось отправить электронное письмо. Пожалуйста, "
                                       "проверьте журналы для получения дополнительной информации.")

    def send_email_with_images(self, chat_id, recipients, email_subject, email_body, images):
        try:
            msg = EmailMessage()
            msg['From'] = EMAIL_USERNAME
            msg['To'] = recipients
            msg['Subject'] = email_subject
            msg.set_content(email_body)

            for image_data, image_extension in images:
                # Add each image as an attachment to the email
                msg.add_attachment(image_data, maintype='image', subtype=image_extension)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, context=context) as smtp:
                smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                smtp.send_message(msg)

            self.send_message(chat_id, "Email sent successfully!"
                                       "\nЭлектронное письмо успешно отправлено!")
        except Exception as e:
            logger.error(f"Failed to send the email: {str(e)}"
                         f"\nНе удалось отправить электронное письмо: {str(e)}")
            self.bot.send_message(chat_id, "Failed to send the email. Please check the logs for more information."
                                           "\nНе удалось отправить электронное письмо. "
                                           "Пожалуйста, проверьте журналы для получения дополнительной информации.")


# Create an instance of BotHandler
bot_handler = BotHandler(bot)


# Handle the '/start' command
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot_handler.send_email(message)


# Start the bot
bot.polling()
