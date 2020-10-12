import telebot
import smtplib
import imaplib
import time
import email
import base64
import re
from threading import Thread


class MailThread(Thread):
    """
    Пример многопоточной загрузки файлов из интернета
    """

    def __init__(self):
        """Инициализация потока"""
        Thread.__init__(self)

    def run(self):
        """Запуск потока"""
        server_imap.login(user, password)
        while True:
            time.sleep(5)
            server_imap.list()
            server_imap.select("INBOX", readonly=False)
            result, data = server_imap.search(None, "ALL")
            ids = data[0]
            id_list = ids.split()
            for mail_id in id_list:
                result, data = server_imap.fetch(mail_id, "(RFC822)")
                raw_email = data[0][1]
                try:
                    email_message = email.message_from_string(raw_email)
                except TypeError:
                    email_message = email.message_from_bytes(raw_email)
                if email_message['Content-Transfer-Encoding'] == 'base64':
                    if '=?utf-8?b?' in email_message['Subject']:
                        subject = re.sub('=\?utf-8\?b\?', '', re.sub('\?=', '', email_message['Subject']))
                    else:
                        subject = email_message['Subject']
                    subject = ''.join([base64.b64decode(x).decode('utf-8') for x in subject.split()])
                else:
                    subject = email_message['Subject'].decode('utf-8')
                print(subject)
                body = email_message.get_payload()
                mail_data = base64.b64decode(body).decode('utf8')
                print(mail_data)


def send_email(host, username, password, subject, to_addr, body_text):
    """
    Send an email
    """

    BODY = "\r\n".join((
        "From: %s" % username,
        "To: %s" % to_addr,
        "Subject: %s" % subject,
        "",
        body_text
    ))

    server = smtplib.SMTP_SSL(host)
    server.set_debuglevel(1)
    server.ehlo(username)
    server.login(username, password)
    server.auth_plain()
    server.sendmail(username, [to_addr], BODY)
    server.quit()


# telegram api token: 1210138657:AAG-4Ra3LKYquRHi4FgnMttiRe2JHFpi_9Y
bot = telebot.TeleBot('1210138657:AAG-4Ra3LKYquRHi4FgnMttiRe2JHFpi_9Y')
server_smtp = 'smtp.yandex.ru'
user = 'Stuninformer@yandex.ru'
password = '257686494734'
server_imap = imaplib.IMAP4_SSL('imap.yandex.ru')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/help":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/start":
        bot.send_message(message.from_user.id, "Напиши привет")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")
    with open('users.txt', 'w') as file:
        file.write(str(message.from_user.id))


mail_thread = MailThread()
mail_thread.start()

bot.polling(none_stop=True, interval=0)



