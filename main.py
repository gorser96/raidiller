# coding=utf-8
import cv2
import numpy as np
import pyautogui
import win32gui
import smtplib
from PIL import ImageGrab
from numpy import uint8
from numpy.ma import array
from time import sleep
from ctypes import windll
import game_interface
import game_module


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
    # color_from = (17, 46, 82)
    # color_to = (27, 57, 92)
    # mask = cv2.inRange(img, color_from, color_to)
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    # closed = cv2.erode(mask, kernel, iterations=1)
    # (centers, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # rectangles = [cv2.boundingRect(x) for x in centers]
    # rectangles.remove(max(rectangles, key=lambda x: x[2] * x[3]))
    # rectangles.remove(min(rectangles, key=lambda x: x[2] * x[3]))
    # rect_team1 = max(rectangles, key=lambda x: x[0])
    # rect_team2 = min(rectangles, key=lambda x: x[1])
    # rect_team3 = max(rectangles, key=lambda x: x[1])
    # rect_team4 = min(rectangles, key=lambda x: x[0])
    # img_team1 = img[
    #             rect_team1[1]:rect_team1[1] + rect_team1[3],
    #             rect_team1[0]: rect_team1[0] + rect_team1[2]]
    # img_team2 = img[
    #             rect_team2[1]:rect_team2[1] + rect_team2[3],
    #             rect_team2[0]: rect_team2[0] + rect_team2[2]]
    # img_team3 = img[
    #             rect_team3[1]:rect_team3[1] + rect_team3[3],
    #             rect_team3[0]: rect_team3[0] + rect_team3[2]]
    # img_team4 = img[
    #             rect_team4[1]:rect_team4[1] + rect_team4[3],
    #             rect_team4[0]: rect_team4[0] + rect_team4[2]]
    #
    # img_team1_r = cv2.resize(img_team1, (rect_team1[2] * 2, rect_team1[3] * 2))
    # img_team2_r = cv2.resize(img_team2, (rect_team2[2] * 2, rect_team2[3] * 2))
    #
    # gray1 = cv2.cvtColor(img_team1_r, cv2.COLOR_BGR2GRAY)
    # gray2 = cv2.cvtColor(img_team2_r, cv2.COLOR_BGR2GRAY)
    # _, threshold1 = cv2.threshold(gray1, 195, 250, cv2.THRESH_BINARY)
    # _, threshold2 = cv2.threshold(gray2, 195, 250, cv2.THRESH_BINARY)
    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    # closed1 = cv2.dilate(threshold1, kernel, iterations=1)
    # closed2 = cv2.dilate(threshold2, kernel, iterations=1)
    # cv2.imshow('team1c', closed1)
    # cv2.imshow('team2c', closed2)
    # (contours1, _) = cv2.findContours(closed1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # (contours2, _) = cv2.findContours(closed2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # net = cv2.ml.KNearest_load('knearest.data')
    # lvl_s = ''
    # for contour in contours1:
    #     area = cv2.contourArea(contour)
    #     if 100 < area < 400:
    #         x, y, w, h = cv2.boundingRect(contour)
    #         digit = gray1[y:y+h, x:x+w]
    #         digit_r = cv2.resize(digit, (10, 10))
    #         digit_r_t = digit_r.reshape((1, 100))
    #         digit_r_t = np.float32(digit_r_t)
    #         retval, results, neigh_resp, dists = net.findNearest(digit_r_t, k=1)
    #         lvl_s += str(int((results[0][0])))
    #         cv2.rectangle(gray1, (x, y), (x + w, y + h), (0, 255, 0), 1)
    # cv2.imshow('gray1', gray1)
    # print(int(lvl_s))
    # lvl_s = ''
    # for contour in contours2:
    #     area = cv2.contourArea(contour)
    #     if 100 < area < 400:
    #         x, y, w, h = cv2.boundingRect(contour)
    #         digit = gray2[y:y+h, x:x+w]
    #         digit_r = cv2.resize(digit, (10, 10))
    #         digit_r_t = digit_r.reshape((1, 100))
    #         digit_r_t = np.float32(digit_r_t)
    #         retval, results, neigh_resp, dists = net.findNearest(digit_r_t, k=1)
    #         lvl_s += str(int((results[0][0])))
    #         cv2.rectangle(gray2, (x, y), (x + w, y + h), (0, 255, 0), 1)
    # cv2.imshow('gray2', gray2)
    # print(int(lvl_s))

    # raid = game_interface.RaidWindow()
    # raid.initialize_positions()

    game_module.initialize()
    # game_module.focus_raid()
    sleep(0.5)
    # game_module.feature_thread()
    # game_module.auto_configure()

    print('Выполнить автоматическую конфигурацию? (y/n)')
    answer = input()
    if answer == 'y':
        game_module.focus_raid()
        game_module.auto_configure()
    else:
        game_module.focus_raid()
        game_module.configure()
        print('Выполнить переход к локации? (y/n)')
        answer = input()
        if answer == 'y':
            game_module.focus_raid()
            game_module.go_main_actions()
            game_module.go_actions_campaign()
            game_module.go_campaign_location()
            game_module.go_location_level()
        is_first = True
        is_exit = False
        while not is_exit:
            print('Input count of fights or q for exit: ')
            inp = input()
            if inp == "q":
                is_exit = True
            else:
                count_fights = int(inp)
                if count_fights < 1:
                    print('Incorrect value!')
                    continue
                elif count_fights > 110:
                    print('Are you sure about this? (y/n)')
                    accept = input()
                    if accept != "y":
                        continue
                game_module.focus_raid()
                if is_first:
                    game_module.click_start()
                else:
                    game_module.click_repeat()
                is_first = False
                for index in range(0, count_fights - 1):
                    print('Current iteration: {}'.format(index + 1))
                    game_module.wait_fighting()
                    game_module.click_repeat()
                    sleep(3)

    cv2.waitKey(0)
