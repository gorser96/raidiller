# coding=utf-8
import cv2
import numpy as np
import win32gui
import pyautogui
import math
from enums import CampaignDifficult, RaidScreen
from point import Point
from numpy import uint8
from numpy.ma import array
from ctypes import windll
from time import sleep
from PIL import ImageGrab


class RaidWindow:
    """
    Класс работы с окном игры
    """
    __name_of_window = "Raid: Shadow Legends"
    __window_info = None
    __fight_btn_position = None
    __campaign_btn_position = None
    __dungeon_btn_position = None
    __difficult_position = None
    __difficult_list_position = None
    __sulfur_trail_position = None
    __sulfur_trail_lvl_position = None
    __team1_position = None
    __team2_position = None
    __team3_position = None
    __team4_position = None
    __collection_position = None
    __start_btn_position = None
    __repeat_btn_position = None

    __template_method = cv2.TM_CCOEFF_NORMED
    __selected_difficult = CampaignDifficult.IMPOSSIBLE
    __selected_lvl = 6
    __current_screen = RaidScreen.MAIN_MENU

    def __set_window_coordinates(self, hwnd, _):
        """
        Callback функция для перебора открытых окон, выполняет поиск окна игры
        """
        if win32gui.IsWindowVisible(hwnd):
            if self.__name_of_window in win32gui.GetWindowText(hwnd):
                rect = win32gui.GetWindowRect(hwnd)
                x = rect[0]
                y = rect[1]
                w = rect[2] - x
                h = rect[3] - y
                self.__window_info = Point(x, y, w, h)
                win32gui.SetForegroundWindow(hwnd)

    def __get_screen(self):
        """
        Получение скриншота окна игры
        """
        box = (self.__window_info.x + 8,
               self.__window_info.y + 40,
               self.__window_info.x + self.__window_info.width - 8,
               self.__window_info.y + self.__window_info.height - 8)
        screen = ImageGrab.grab(box)
        img = array(screen.getdata(), dtype=uint8).reshape((screen.size[1], screen.size[0], 3))
        return img

    def __get_object_position(self, source_img, template_img):
        """
        Получение позиции кнопки (поиск по шаблону)
        :param source_img: Окно игры
        :param template_img: Шаблон из файла
        :return: Найденная позиция (класс Point)
        """
        width_src, height_src = source_img.shape[::-1]
        width_template, height_template = template_img.shape[::-1]
        canny_img = cv2.Canny(source_img, 150, 250)
        canny_template = cv2.Canny(template_img, 150, 250)
        max_loc = None
        max_val = 0
        max_scale_w = 1
        max_scale_h = 1
        for scale in np.linspace(0.4, 1.0, 20)[::-1]:
            # resize the image according to the scale, and keep track
            # of the ratio of the resizing
            width_scaled = int(width_src * scale)
            height_scaled = int(height_src * scale)
            if width_template > width_scaled or height_template > height_scaled:
                break
            re_scale_w = width_src / width_scaled
            re_scale_h = height_src / height_scaled
            resized = cv2.resize(canny_img, (width_scaled, height_scaled), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(resized, canny_template, self.__template_method)
            _, _maxVal, _, _maxLoc = cv2.minMaxLoc(result)
            if _maxVal > max_val:
                max_loc = _maxLoc
                max_scale_h = re_scale_h
                max_scale_w = re_scale_w
            threshold = 0.4
            loc = np.where(result >= threshold)
            list_loc = list(zip(*loc[::-1]))
            if len(list_loc) > 1:
                min_loc = min(list_loc)
                return Point(int(min_loc[0] * re_scale_w),
                             int(min_loc[1] * re_scale_h),
                             int(width_template * re_scale_w),
                             int(height_template * re_scale_h))
            elif len(list_loc) == 0:
                continue
            else:
                return Point(int(list_loc[0][0] * re_scale_w),
                             int(list_loc[0][1] * re_scale_h),
                             int(width_template * re_scale_w),
                             int(height_template * re_scale_h))
        return Point(int(max_loc[0] * max_scale_w),
                     int(max_loc[1] * max_scale_h),
                     int(width_template * max_scale_w),
                     int(height_template * max_scale_h))

    def __show_position(self, position_btn):
        """
        Отладочная функция для отображения прямоугольника кнопки
        :param position_btn: позиция кнопки (класс Point)
        """
        raid_screenshot = self.__get_screen()
        cv2.rectangle(raid_screenshot,
                      position_btn.top(),
                      position_btn.bottom(),
                      (0, 255, 255),
                      2)
        cv2.imshow("show_position", raid_screenshot)

    def __click_position(self, position_btn):
        """
        перемещение курсора на центр кнопки и нажатие на нее
        """
        pos = position_btn.center()
        pyautogui.moveTo(pos[0] + self.__window_info.x,
                         pos[1] + self.__window_info.y + 40,
                         duration=0.17)
        pyautogui.click()

    def __extract_rectangle(self, position_btn):
        """
        Извлечение части изображения
        :param position_btn: кнопка/объект который нужно извлечь
        :return: Opencv изображение
        """
        raid_screenshot = self.__get_screen()
        return raid_screenshot[
               position_btn.y:position_btn.y + position_btn.height,
               position_btn.x:position_btn.x + position_btn.width]

    def __calculate_difficult_row(self):
        """
        Расчет координат строки с нужной сложностью
        :return: Point
        """
        diff_row = Point(0, 0, 0, 0)
        height = self.__difficult_list_position.height
        diff_row.x = self.__difficult_list_position.x
        diff_row.width = self.__difficult_list_position.width
        # всего 4 уровня сложности, высота строки одинаковая
        diff_row.height = int(height / 4)
        diff_row.y = self.__difficult_list_position.y + diff_row.height * (self.__selected_difficult - 1)
        return diff_row

    def __extract_color(self, color):
        """
        Выделение указанного цвета (с небольшим диапазоном) на скриншоте игры
        :param color: Цвет для выделения
        :return: Маска экрана игры, где белый цвет - цвет выделения
        """
        raid_screenshot = self.__get_screen()
        color_lower = (0 if color[0] <= 2 else color[0] - 3,
                       0 if color[1] <= 2 else color[1] - 3,
                       0 if color[2] <= 2 else color[2] - 3)
        color_upper = (255 if color[0] >= 253 else color[0] + 3,
                       255 if color[1] >= 253 else color[1] + 3,
                       255 if color[2] >= 253 else color[2] + 3)
        mask = cv2.inRange(raid_screenshot, color_lower, color_upper)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        result = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
        return result

    def __get_actions_rectangles(self):
        """
        Возвращает координаты прямоугольников с игровыми активностями (Кампания, войны фракции и т.д.)
        :return: Array of (x, y, width, height)
        """
        if self.__current_screen != RaidScreen.ACTIONS:
            return None
        closed = self.__extract_color((5, 37, 58))
        contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = list(filter(lambda x: cv2.contourArea(x) > 200, contours))
        contour_rectangles = [cv2.boundingRect(x) for x in contours]
        contours_remove = list(filter(
            lambda contour_rect: len(list(filter(
                lambda x: x[0] < contour_rect[0] < x[0] + x[2],
                contour_rectangles))) > 0,
            contour_rectangles))

        for contour in contours_remove:
            contour_rectangles.remove(contour)

        return contour_rectangles

    def __get_difficult_rectangle(self):
        """
        Выполняет поиск кнопки выбора уровня сложности в кампании
        :return: (x, y, width, height)
        """
        if self.__current_screen != RaidScreen.CAMPAIGN:
            return None
        raid_screenshot = self.__get_screen()
        gray = cv2.cvtColor(raid_screenshot, cv2.COLOR_BGR2GRAY)
        canny = cv2.Canny(gray, 200, 240)
        contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = list(filter(lambda x: cv2.contourArea(x) > 200, contours))
        contours_filtered = []
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            # получение массива углов фигуры
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            if len(approx) == 4:
                contours_filtered.append(contour)
        bounded_contours = [cv2.boundingRect(x) for x in contours_filtered]
        dif_contour = min(bounded_contours, key=lambda x: x[0])
        return dif_contour

    def set_difficult(self, name):
        """
        Установить сложность кампании для фарма
        :param name: Название сложности из игры (обычный, трудный и т.д.)
        """
        if name.lower() == 'обычный':
            self.__selected_difficult = CampaignDifficult.SIMPLE
        elif name.lower() == 'трудный':
            self.__selected_difficult = CampaignDifficult.HARD
        elif name.lower() == 'невозможный':
            self.__selected_difficult = CampaignDifficult.IMPOSSIBLE
        elif name.lower() == 'адский':
            self.__selected_difficult = CampaignDifficult.HELL
        else:
            print('Unknown difficult! Setting default: Impossible')
            self.__selected_difficult = CampaignDifficult.IMPOSSIBLE

    def set_level(self, lvl):
        """
        Установить уровень для прохождения (1, 2, 3 и т.д.)
        """
        self.__selected_lvl = lvl

    def initialize_positions(self):
        """
        Инициализация класса для работы с окном игры
        """
        # отключение масштабирования экрана, для корректной работы с координатами
        user32 = windll.user32
        user32.SetProcessDPIAware()
        win32gui.EnumWindows(self.__set_window_coordinates, None)
        pause = 1.3
        print('Detected raid window: {} {}'.format(self.__window_info.x, self.__window_info.y))
        # ожидание переключения окна
        sleep(0.2)

        raid_screenshot = self.__get_screen()
        gray_screenshot = cv2.cvtColor(raid_screenshot, cv2.COLOR_BGR2GRAY)
        width, height = gray_screenshot.shape[::-1]
        harris_corners = cv2.cornerHarris(gray_screenshot, 3, 3, 0.05)
        harris_corners = cv2.dilate(harris_corners, None)
        _, harris_corners = cv2.threshold(harris_corners, 0.06 * harris_corners.max(), 255, 0)
        harris_corners = np.uint8(harris_corners)
        _, labels, stats, centroids = cv2.connectedComponentsWithStats(harris_corners)
        blank_image = np.zeros((height, width, 3), np.uint8)
        centroids_of_centroids = [[] for i in centroids]
        for index in range(len(centroids_of_centroids)):
            centroids_of_centroids[index].append(index)
        for centroid in centroids:
            x, y = centroid
            cv2.circle(blank_image, (int(x), int(y)), 5, (255, 255, 255), -1)
        cv2.imshow('123', blank_image)
        length = len(centroids)
        for index1 in range(length - 1):
            x1, y1 = centroids[index1]
            for index2 in range(index1 + 1, length):
                x2, y2 = centroids[index2]
                distance = math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))
                if distance < 100:
                    centroids_of_centroids[index1].append(index2)
        length = len(centroids_of_centroids)
        for index1 in range(length - 1):
            for index2 in range(index1 + 1, length):
                if len(list(set(centroids_of_centroids[index1]) & set(centroids_of_centroids[index2]))) > 0:
                    centroids_of_centroids[index1] = list(
                        set(centroids_of_centroids[index1] + centroids_of_centroids[index2]))
                    centroids_of_centroids[index2] = [index2]
        centroids_of_centroids = list(filter(lambda item: 1 < len(item) < 40, centroids_of_centroids))
        for item in centroids_of_centroids:
            points = [centroids[val] for val in item]
            x = int(min(points, key=lambda point: point[0])[0])
            y = int(min(points, key=lambda point: point[1])[1])
            w = int(max(points, key=lambda point: point[0])[0]) - x
            h = int(max(points, key=lambda point: point[1])[1]) - y
            cv2.rectangle(raid_screenshot, (x, y), (x+w, y+h), (0, 255, 0), 1)
        cv2.imshow('test', raid_screenshot)
        cv2.waitKey(0)
        kernel = np.ones((10, 10), np.uint8)
        ret, dst = cv2.threshold(harris_corners, 0.06 * harris_corners.max(), 255, 0)
        dst = cv2.dilate(dst, kernel, iterations=3)
        raid_screenshot[dst > 0.05 * dst.max()] = [255, 255, 255]
        gray_screenshot = cv2.cvtColor(raid_screenshot, cv2.COLOR_BGR2GRAY)
        raid_screenshot = self.__get_screen()
        _, thresh = cv2.threshold(gray_screenshot, 250, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_dist = 50
        length = len(contours)
        status = np.zeros((length, 1))
        for i, cnt1 in enumerate(contours):
            x = i
            if i != length - 1:
                for j, cnt2 in enumerate(contours[i + 1:]):
                    x = x + 1
                    # написать все условия с координатами и вычисления к ним
                    if dist == True:
                        val = min(status[i], status[x])
                        status[x] = status[i] = val
                    else:
                        if status[x] == status[i]:
                            status[x] = i + 1
        unified = []
        maximum = int(status.max()) + 1
        for i in range(maximum):
            pos = np.where(status == i)[0]
            if pos.size != 0:
                cont = np.vstack(contours[i] for i in pos)
                hull = cv2.convexHull(cont)
                unified.append(hull)

        for contour in unified:
            x, y, w, h = cv2.boundingRect(contour)
            # M = cv2.moments(contour)
            # cX = int(M["m10"] / M["m00"])
            # cY = int(M["m01"] / M["m00"])
            # cv2.circle(raid_screenshot, (cX, cY), 5, (0, 255, 0), -1)
            cv2.rectangle(raid_screenshot, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.imshow('Harris Corners', raid_screenshot)
        # cv2.imshow('Harris Corners1', dst)
        # harris_corners = cv2.dilate(harris_corners, kernel, iterations=2)
        # raid_screenshot[harris_corners > 0.05 * harris_corners.max()] = [255, 127, 127]
        # cv2.imshow('Harris Corners', raid_screenshot)
        # canny = cv2.Canny(gray_screenshot, 50, 150)
        # contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # contours = list(filter(lambda x: cv2.contourArea(x) > 100, contours))
        # cv2.drawContours(raid_screenshot, contours, -1, (0, 255, 0), 1)
        # for contour in contours:
        #     x, y, w, h = cv2.boundingRect(contour)
        #     cv2.rectangle(raid_screenshot, (x, y), (x + w, y+h), (0, 255, 0), 1)
        cv2.waitKey(0)
        self.__current_screen = RaidScreen.MAIN_MENU
        # поиск кнопки "Бой"
        template_img = cv2.imread('sources\\fight_btn.png', cv2.IMREAD_GRAYSCALE)
        raid_screenshot = self.__get_screen()
        # корректирование снимка окна в серый цвет, необходимо для работы MatchTemplate
        gray_screenshot = cv2.cvtColor(raid_screenshot, cv2.COLOR_BGR2GRAY)
        self.__fight_btn_position = self.__get_object_position(gray_screenshot, template_img)
        if self.__fight_btn_position is None:
            print('Кнопка "Бой" не найдена!')
            return False
        else:
            print('Detected fight button: {} {}'.format(self.__fight_btn_position.x, self.__fight_btn_position.y))
        self.__click_position(self.__fight_btn_position)
        sleep(pause)
        self.__current_screen = RaidScreen.ACTIONS

        # поиск кнопки "Кампания" и "Подземелье"
        action_rectangles = self.__get_actions_rectangles()
        action_rectangles.sort(key=lambda x: x[0])
        self.__campaign_btn_position = Point(action_rectangles[0][0],
                                             action_rectangles[0][1],
                                             action_rectangles[0][2],
                                             action_rectangles[0][3])
        self.__dungeon_btn_position = Point(action_rectangles[1][0],
                                            action_rectangles[1][1],
                                            action_rectangles[1][2],
                                            action_rectangles[1][3])
        if self.__campaign_btn_position is None:
            print('Кнопка "Кампания" не найдена!')
            return False
        else:
            print('Detected campaign button: {} {}'
                  .format(self.__campaign_btn_position.x, self.__campaign_btn_position.y))
        self.__click_position(self.__campaign_btn_position)
        sleep(pause)
        self.__current_screen = RaidScreen.CAMPAIGN

        # установка уровня сложности
        x, y, width, height = self.__get_difficult_rectangle()
        self.__difficult_position = Point(x, y, width, height)
        if self.__difficult_position is None:
            print('Кнопка выбора сложности не найдена!')
            return False
        else:
            print('Detected difficult button: {} {}'
                  .format(self.__difficult_position.x, self.__difficult_position.y))
        self.__click_position(self.__difficult_position)
        sleep(pause)
        closed = self.__extract_color((36, 47, 59))
        contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_box = max(contours, key=lambda contour: cv2.contourArea(contour))
        x, y, width, height = cv2.boundingRect(max_box)
        self.__difficult_list_position = Point(x, y, width, height)
        self.__click_position(self.__difficult_position)
        sleep(pause)

        # Скролл до серной тропы
        for index in range(0, 3):
            x = self.__window_info.x + self.__window_info.width - 70
            y = self.__window_info.y + self.__window_info.height / 2
            pyautogui.moveTo(x, y, 2)
            pyautogui.mouseDown()
            pyautogui.moveTo(self.__window_info.x + 80, y, 2)
            pyautogui.mouseUp()
            sleep(0.3)

        # поиск кнопки "Серная тропа"
        template_img = cv2.imread('sources\\sulfur_trail.png', cv2.IMREAD_GRAYSCALE)
        raid_screenshot = self.__get_screen()
        gray_screenshot = cv2.cvtColor(raid_screenshot, cv2.COLOR_BGR2GRAY)
        self.__sulfur_trail_position = self.__get_object_position(gray_screenshot, template_img)
        if self.__sulfur_trail_position is None:
            print('Кнопка "Серная тропа" не найдена!')
            return False
        else:
            print('Detected sulfur trail button: {} {}'.format(self.__sulfur_trail_position.x,
                                                               self.__sulfur_trail_position.y))
        self.__click_position(self.__sulfur_trail_position)
        sleep(pause)
        self.__current_screen = RaidScreen.CAMPAIGN_LEVEL

        # Скролл до нужного уровня на локации
        template_img = cv2.imread('sources\\sulfur_trail_6_lvl.png', cv2.IMREAD_GRAYSCALE)
        width, height = template_img.shape[::-1]
        if self.__selected_lvl > 4:
            pyautogui.moveTo(self.__window_info.center()[0],
                             self.__window_info.y + self.__window_info.height - height,
                             1.7)
            pyautogui.mouseDown()
            pyautogui.moveTo(self.__window_info.center()[0],
                             self.__window_info.y + height,
                             2)
            pyautogui.mouseUp()
        sleep(pause)

        raid_screenshot = self.__get_screen()
        color_from = (10, 70, 100)
        color_to = (20, 80, 110)
        mask = cv2.inRange(raid_screenshot, color_from, color_to)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        closed = cv2.erode(closed, kernel, iterations=1)
        closed = cv2.dilate(closed, kernel, iterations=1)
        white_points = np.argwhere(closed == 255)
        x1 = min(x[1] for x in white_points)
        y1 = min(x[0] for x in white_points)
        y2 = max(x[0] for x in white_points)
        if self.__selected_lvl > 4:
            cur_lvl = 8 - self.__selected_lvl
            self.__sulfur_trail_lvl_position = Point(x1, y2 - cur_lvl * height, width, height)
        else:
            self.__sulfur_trail_lvl_position = Point(x1, y1 + self.__selected_lvl * height, width, height)
        if self.__sulfur_trail_lvl_position is None:
            print('Строка "Уровень Серной тропы" не найдена!')
            return False
        else:
            print('Detected sulfur level trail row: {} {}'.format(self.__sulfur_trail_lvl_position.x,
                                                                  self.__sulfur_trail_lvl_position.y))

        # Поиск и нажатие на кнопку "Начать"
        template_img = cv2.imread('sources\\start_btn.png', cv2.IMREAD_GRAYSCALE)
        part_raid_screenshot = self.__extract_rectangle(self.__sulfur_trail_lvl_position)
        part_gray_screenshot = cv2.cvtColor(part_raid_screenshot, cv2.COLOR_BGR2GRAY)
        start_btn_pos = self.__get_object_position(part_gray_screenshot, template_img)
        start_btn_pos.x += self.__sulfur_trail_lvl_position.x
        start_btn_pos.y += self.__sulfur_trail_lvl_position.y
        self.__sulfur_trail_lvl_position = start_btn_pos

        if self.__sulfur_trail_lvl_position is None:
            print('Кнопка "Уровень Серной тропы" не найдена!')
            return False
        else:
            print('Detected sulfur level trail button: {} {}'.format(self.__sulfur_trail_lvl_position.x,
                                                                     self.__sulfur_trail_lvl_position.y))
        self.__click_position(self.__sulfur_trail_lvl_position)
        sleep(0.5)
        self.__current_screen = RaidScreen.PRE_FIGHT

        # Поиск иконок команды героев
        raid_screenshot = self.__get_screen()
        color_from = (17, 46, 82)
        color_to = (27, 57, 92)
        mask = cv2.inRange(raid_screenshot, color_from, color_to)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        closed = cv2.erode(mask, kernel, iterations=1)
        (centers, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rectangles = [cv2.boundingRect(x) for x in centers]
        rectangles.remove(max(rectangles, key=lambda x: x[2] * x[3]))
        rectangles.remove(min(rectangles, key=lambda x: x[2] * x[3]))
        rect_team1 = max(rectangles, key=lambda x: x[0])
        rect_team2 = min(rectangles, key=lambda x: x[1])
        rect_team3 = max(rectangles, key=lambda x: x[1])
        rect_team4 = min(rectangles, key=lambda x: x[0])
        self.__team1_position = Point(rect_team1[0], rect_team1[1], rect_team1[2], rect_team1[3])
        self.__team2_position = Point(rect_team2[0], rect_team2[1], rect_team2[2], rect_team2[3])
        self.__team3_position = Point(rect_team3[0], rect_team3[1], rect_team3[2], rect_team3[3])
        self.__team4_position = Point(rect_team4[0], rect_team4[1], rect_team4[2], rect_team4[3])

        # Поиск кнопки "Начать"
        raid_screenshot = self.__get_screen()
        color_from = (176, 114, 0)
        color_to = (186, 130, 6)
        mask = cv2.inRange(raid_screenshot, color_from, color_to)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.erode(mask, kernel, iterations=1)
        (centers, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rectangles = [cv2.boundingRect(x) for x in centers]
        btn_rect = max(rectangles, key=lambda x: x[2] * x[3])
        self.__start_btn_position = Point(btn_rect[0], btn_rect[1], btn_rect[2], btn_rect[3])
        if self.__start_btn_position is None:
            print('Кнопка "Начать" не найдена!')
            return False
        else:
            print('Detected start button: {} {}'.format(self.__start_btn_position.x, self.__start_btn_position.y))

        # Поиск коллекции
        color_from = (16, 76, 107)
        color_to = (18, 78, 109)
        mask = cv2.inRange(raid_screenshot, color_from, color_to)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        closed = cv2.erode(mask, kernel, iterations=1)
        white_points = np.argwhere(closed == 255)
        x = min([item[1] for item in white_points])
        y1 = min([item[0] for item in white_points])
        y2 = max([item[0] for item in white_points])
        self.__collection_position = Point(x, y1, self.__start_btn_position.x - x, y2 - y1)
        if self.__collection_position is None:
            print('Коллекция героев не найдена!')
            return False
        else:
            print('Detected collection: {} {}'.format(self.__collection_position.x, self.__collection_position.y))

        return True
