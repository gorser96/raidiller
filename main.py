# coding=utf-8
import smtplib
import game_module
from point import Point
import time
import sys
from PyQt5.QtWidgets import QApplication
import gui


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

    server = smtplib.SMTP_SSL('smtp.yandex.com')
    server.set_debuglevel(1)
    server.ehlo(username)
    server.login(username, password)
    server.auth_plain()
    server.sendmail(username, [to_addr], BODY)
    server.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = gui.MainWindow()
    sys.exit(app.exec_())
