# coding=utf-8
import cv2
import numpy as np
import pytesseract
import os
import itertools
from skimage.measure import compare_ssim

from point import Point
import math
from test_utils import test_show, test_draw_rect, test_draw_point

__template_method = cv2.TM_CCOEFF_NORMED


def __extract_colors(source_img, color_lower, color_upper, color_type=None):
    processing_img = source_img.copy()
    if color_type is not None:
        processing_img = cv2.cvtColor(source_img, color_type)
    mask = cv2.inRange(processing_img, color_lower, color_upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    result = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
    return result


def __extract_color(source_img, color):
    """
    Выделение указанного цвета (с небольшим диапазоном) на скриншоте игры
    :param source_img: Источник изображения
    :param color: Цвет для выделения
    :return: Маска экрана игры, где белый цвет - цвет выделения
    """
    color_lower = (0 if color[0] <= 2 else color[0] - 3,
                   0 if color[1] <= 2 else color[1] - 3,
                   0 if color[2] <= 2 else color[2] - 3)
    color_upper = (255 if color[0] >= 253 else color[0] + 3,
                   255 if color[1] >= 253 else color[1] + 3,
                   255 if color[2] >= 253 else color[2] + 3)
    return __extract_colors(source_img, color_lower, color_upper)


def is_ad(source_img):
    _, width, height = source_img.shape[::-1]
    cropped = source_img[0:int(height * 0.5), int(width/2):width]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 180, 250)
    circles = cv2.HoughCircles(canny,
                               cv2.HOUGH_GRADIENT,
                               1,
                               width / 8,
                               param1=100, param2=25,
                               minRadius=5, maxRadius=60)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        circles = circles[0, :]  # 0 - x; 1 - y; 2 - radius
        mask_close = __extract_color(cropped, (216, 206, 156))
        contours, _ = cv2.findContours(mask_close, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            # получение массива углов фигуры
            approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
            if len(approx) > 6:
                m = cv2.moments(contour)
                c_x = int(m["m10"] / m["m00"])
                c_y = int(m["m01"] / m["m00"])
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(cropped, [box], 0, (0, 0, 255), 2)
                # rect_points = [approx[0], approx[2], approx[4], approx[6]]
                edge1 = np.int0((box[1][0] - box[0][0], box[1][1] - box[0][1]))
                edge2 = np.int0((box[2][0] - box[1][0], box[2][1] - box[1][1]))
                used_edge = edge1
                if cv2.norm(edge2) > cv2.norm(edge1):
                    used_edge = edge2
                reference = (1, 0)  # горизонтальный вектор, задающий горизонт
                angle = 180.0 / math.pi * math.acos(
                    (reference[0] * used_edge[0] + reference[1] * used_edge[1]) /
                    (cv2.norm(reference) * cv2.norm(used_edge)))
                if math.fabs(angle - 180) > 10:
                    return False
                for circle in circles:
                    if math.hypot(c_x - circle[0], c_y - circle[1]) <= circle[2]:
                        return True
                # x, y, w, h = cv2.boundingRect(contour)
                # cv2.rectangle(source_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # test_show(source_img)
    return False


def is_main_menu(source_img):
    mask = __extract_color(source_img, (157, 152, 137))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda contour: cv2.contourArea(contour) > 200, contours))
    if len(contours) == 0:
        return False
    total_area = sum([cv2.contourArea(item) for item in contours])
    _, width, height = source_img.shape[::-1]
    cropped = source_img[int(height * 0.3):int(height * 0.6), 0:int(width * 0.1)]
    extracted = __extract_color(cropped, (16, 40, 50))
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return False
    max_contour = max(contours, key=lambda item: cv2.contourArea(item))
    x, y, w, h = cv2.boundingRect(max_contour)
    area1 = cv2.contourArea(max_contour)
    area2 = w * h
    ratio = area1 / area2
    return total_area > 3000 and ratio > 0.85


def get_battle_btn(source_img):
    color_lower = (50, 0, 0)
    color_upper = (190, 20, 20)
    extracted = __extract_colors(source_img, color_lower, color_upper)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cv2.boundingRect(item) for item in contours]
    max_contour = max(contours, key=lambda item: item[2] * item[3])
    return max_contour


def __get_circles(source_img):
    _, width, height = source_img.shape[::-1]
    gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(blur,
                               cv2.HOUGH_GRADIENT,
                               1,
                               height / 8,
                               param1=70,
                               param2=20,
                               minRadius=10,
                               maxRadius=60)
    circles_area = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # circle outline
            radius = i[2]
            circles_area.append(math.pi * math.pow(radius, 2))
    mask = __extract_color(source_img, (27, 34, 39))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 200, contours))
    result_circles = []
    for contour in contours:
        if len(contour) > 4:
            center, axes, angle = cv2.fitEllipse(contour)
            r1, r2 = np.uint16([axes[0] / 2, axes[1] / 2])
            cnt_area = math.pi * r1 * r2
            for circle_area in circles_area:
                if math.fabs(cnt_area - circle_area) < 1500:
                    result_circles.append(contour)
    return result_circles


def is_fighting(frame1, frame2):
    frame1_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    frame2_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    (score, diff) = compare_ssim(frame1_gray, frame2_gray, full=True)
    return score < 0.9


def get_object_position(source_img, template_img):
    """
    Получение позиции кнопки (поиск по шаблону)
    :param source_img: Окно игры
    :param template_img: Шаблон из файла
    :return: Найденная позиция (класс Point)
    """
    gray_source = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    width_src, height_src = gray_source.shape[::-1]
    width_template, height_template = gray_template.shape[::-1]
    canny_img = cv2.Canny(gray_source, 150, 250)
    canny_template = cv2.Canny(gray_template, 150, 250)
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
        result = cv2.matchTemplate(resized, canny_template, __template_method)
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
    return None


def get_actions_rectangles(source_img):
    """
    Возвращает координаты прямоугольников с игровыми активностями (Кампания, войны фракции и т.д.)
    Сортировка первый - крайний левый баннер
    :return: Array of (x, y, width, height)
    """
    closed = __extract_color(source_img, (5, 37, 58))
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

    contour_rectangles.sort(key=lambda item: item[0])

    return contour_rectangles


def is_level_selection(source_img):
    """
    Проверка на экран выбора уровня кампании
    :param source_img:
    :return:
    """
    color_from = (10, 70, 100)
    color_to = (20, 80, 110)
    extracted = __extract_colors(source_img, color_from, color_to)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 500, contours))
    if len(contours) == 0:
        return False
    rect_contours = [cv2.boundingRect(item) for item in contours]
    max_contour = max(rect_contours, key=lambda item: item[2] * item[3])
    rect_contours = list(filter(lambda item: math.fabs(item[2] * item[3] - max_contour[2] * max_contour[3]) < 2500,
                                rect_contours))
    return len(rect_contours) > 3


def get_level_position(source_img, level):
    """
    Получает позицию нужного уровня по номеру в кампании
    :param source_img:
    :param level:
    :return: Point
    """
    color_from = (10, 70, 100)
    color_to = (20, 80, 110)
    extracted = __extract_colors(source_img, color_from, color_to)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    rect_contours = [cv2.boundingRect(item) for item in contours]
    max_contour = max(rect_contours, key=lambda item: item[2] * item[3])
    rect_contours = list(filter(lambda item: math.fabs(item[2] * item[3] - max_contour[2] * max_contour[3]) < 2500,
                                rect_contours))
    rect_contours.sort(key=lambda item: item[1])
    if level > 4:
        rect_contours.reverse()
        x, y, w, h = rect_contours[7 - level]
        return Point(x, y, w, h)
    else:
        x, y, w, h = rect_contours[level - 1]
        return Point(x, y, w, h)


def get_start_btn_from_level(source_img):
    """
    Возвращает позицию кнопки "Начать" внутри изображения с уровнем в кампании
    :param source_img: вырезанный из экрана прямоугольник нужного уровня кампании
    :return: Point
    """
    color_from = (10, 70, 100)
    color_to = (20, 80, 110)
    extracted = __extract_colors(source_img, color_from, color_to)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rect_contours = [cv2.boundingRect(item) for item in contours]
    top_right_contour = max(rect_contours, key=lambda item: item[0])
    x, y, w, h = top_right_contour
    return Point(x, y, w, h)


def check_aura_at_start(source_img):
    """
    Проверка на уведомление об отсутствии ауры в команде
    :param source_img:
    :return: (x, y, width, height), (x, y, width, height) - левая и правая кнопки уведомления
    """
    color1 = (20, 123, 156)
    color2 = (0, 112, 148)
    color3 = (5, 115, 150)
    extracted1 = __extract_color(source_img, color1)
    extracted2 = __extract_color(source_img, color2)
    extracted3 = __extract_color(source_img, color3)
    mask = cv2.bitwise_or(extracted1, extracted2)
    mask = cv2.bitwise_or(mask, extracted3)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rect_contours = [cv2.boundingRect(item) for item in contours]
    rect_contours.sort(key=lambda item: item[2] * item[3])
    rect_contours.reverse()
    area1 = rect_contours[0][2] * rect_contours[0][3]
    area2 = rect_contours[1][2] * rect_contours[1][3]
    if math.fabs(area1 - area2) < 200:
        result_rects = [rect_contours[0], rect_contours[1]]
        return min(result_rects, key=lambda item: item[0]), \
               max(result_rects, key=lambda item: item[0])
    return None


def get_difficult_rectangle(source_img):
    """
    Выполняет поиск кнопки выбора уровня сложности в кампании
    :return: Point
    """
    _, width, height = source_img.shape[::-1]
    cropped = source_img[int(height * 0.8):height, 0:int(width * 0.3)]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 150, 240)
    contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda x: cv2.contourArea(x) > 200, contours))
    contours_filtered = []
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        # получение массива углов фигуры
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
        if len(approx) == 4:
            contours_filtered.append(contour)
    if len(contours_filtered) == 0:
        return None
    bounded_contours = [cv2.boundingRect(x) for x in contours_filtered]
    dif_contour = min(bounded_contours, key=lambda x: x[0])
    return Point(dif_contour[0], dif_contour[1] + int(height * 0.8), dif_contour[2], dif_contour[3])


def get_rect_features(source_img):
    """
    Вычисляет прямоугольники по облаку точек из локальных признаков
    :param source_img:
    :return: список типа Point, отсортированный по координате x
    """
    raid_screenshot = source_img.copy()
    _, width, height = raid_screenshot.shape[::-1]
    color_lower = (3, 10, 26)
    color_upper = (6, 16, 29)
    extracted = __extract_colors(raid_screenshot, color_lower, color_upper)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    max_contour = max(contours, key=lambda item: cv2.contourArea(item))
    x, y, w, h = cv2.boundingRect(max_contour)
    y_lower = h
    y_upper = int(height * 0.7)
    cropped = raid_screenshot[y + y_lower:y_upper, 0:width]
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    harris_corners = cv2.cornerHarris(gray, 3, 3, 0.05)
    harris_corners = cv2.dilate(harris_corners, None)
    _, harris_corners = cv2.threshold(harris_corners, 0.06 * harris_corners.max(), 255, 0)
    harris_corners = np.uint8(harris_corners)
    _, labels, stats, centroids = cv2.connectedComponentsWithStats(harris_corners)
    centroids_of_centroids = [[] for i in centroids]
    for index in range(len(centroids_of_centroids)):
        centroids_of_centroids[index].append(index)

    # blank_image = np.zeros((height, width, 3), np.uint8)
    # for centroid in centroids:
    #     x, y = centroid
    #     cv2.circle(blank_image, (int(x), int(y)), 5, (255, 255, 255), -1)
    # cv2.imshow('features', blank_image)

    min_distance = (width * height) / (100 * 115) * 1.2
    length = len(centroids)
    for index1 in range(0, length):
        x1, y1 = centroids[index1]
        for index2 in range(0, length):
            if index1 == index2:
                continue
            x2, y2 = centroids[index2]
            distance = math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))
            if distance < min_distance:
                centroids_of_centroids[index1].append(index2)
    length = len(centroids_of_centroids)
    for index1 in range(0, length):
        for index2 in range(0, length):
            if index1 == index2:
                continue
            if len(list(set(centroids_of_centroids[index1]) & set(centroids_of_centroids[index2]))) > 0:
                centroids_of_centroids[index1] = list(
                    set(centroids_of_centroids[index1] + centroids_of_centroids[index2]))
                centroids_of_centroids[index2] = [index2]
    centroids_of_centroids = list(filter(lambda item: 5 < len(item), centroids_of_centroids))
    result_list = []
    for item in centroids_of_centroids:
        points = [centroids[val] for val in item]
        x = int(min(points, key=lambda point: point[0])[0])
        y = int(min(points, key=lambda point: point[1])[1])
        w = int(max(points, key=lambda point: point[0])[0]) - x
        h = int(max(points, key=lambda point: point[1])[1]) - y
        result_list.append(Point(x, y + y_lower, w, h))
        # cv2.rectangle(cropped, (x, y), (x + w, y + h), (0, 255, 0), 1)
    result_list.sort(key=lambda item: item.x)
    return result_list


def is_pre_fight(source_img):
    """
    Проверка на экран подготовки к бою
    :param source_img:
    :return:
    """
    _, width, height = source_img.shape[::-1]
    cropped = source_img[0:int(height * 0.8), 0:int(width / 2)]
    color_from = (17, 46, 82)
    color_to = (27, 57, 92)
    mask = cv2.inRange(cropped, color_from, color_to)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.erode(mask, kernel, iterations=1)
    (contours, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 200, contours))
    if len(contours) == 0:
        return False
    rectangles = [cv2.boundingRect(x) for x in contours]
    rectangles.remove(max(rectangles, key=lambda x: x[2] * x[3]))
    rectangles.sort(key=lambda rect: rect[2] * rect[3], reverse=True)
    mean = np.mean([rect[2] * rect[3] for rect in rectangles[0:4]])
    rectangles = list(filter(lambda rect: math.fabs(rect[2] * rect[3] / mean - 1) < 0.15,
                             rectangles))
    return 3 < len(rectangles) < 6


def get_icon_teams(source_img):
    """
    Поиск иконок команды героев
    :param source_img:
    :return: Список типа Point, где 0й элемент - герой с аурой, 2й - верхний, 3й - нижний и т.д.
    """
    _, width, height = source_img.shape[::-1]
    cropped = source_img[0:int(height * 0.8), 0:int(width / 2)].copy()
    template_pixel = np.uint8(source_img[int(height / 2), 5])
    # color_from = (17, 46, 82)
    # color_to = (27, 57, 92)
    mask = cv2.inRange(cropped, template_pixel, template_pixel)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    closed = cv2.erode(mask, kernel, iterations=1)
    (contours, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 200, contours))
    if len(contours) == 0:
        return None
    rectangles = [cv2.boundingRect(x) for x in contours]
    rectangles.remove(max(rectangles, key=lambda x: x[2] * x[3]))
    rectangles.sort(key=lambda rect: rect[2] * rect[3], reverse=True)
    mean = np.mean([rect[2] * rect[3] for rect in rectangles[0:4]])
    rectangles = list(filter(lambda rect: math.fabs(rect[2] * rect[3] / mean - 1) < 0.22,
                             rectangles))

    if len(rectangles) == 4:
        rect_team1 = max(rectangles, key=lambda x: x[0])
        rect_team2 = min(rectangles, key=lambda x: x[1])
        rect_team3 = max(rectangles, key=lambda x: x[1])
        rect_team4 = min(rectangles, key=lambda x: x[0])

        team1_position = Point(rect_team1[0], rect_team1[1], rect_team1[2], rect_team1[3])
        team2_position = Point(rect_team2[0], rect_team2[1], rect_team2[2], rect_team2[3])
        team3_position = Point(rect_team3[0], rect_team3[1], rect_team3[2], rect_team3[3])
        team4_position = Point(rect_team4[0], rect_team4[1], rect_team4[2], rect_team4[3])
        return [team1_position, team2_position, team3_position, team4_position]
    elif len(rectangles) == 5:
        y_min = min([rect[1] for rect in rectangles])
        y_max = max([rect[1] for rect in rectangles])

        rect_team1 = max(rectangles, key=lambda x: x[0])
        rect_team2 = sorted(list(filter(lambda rect: math.fabs(rect[1] - y_min) < 10, rectangles)),
                            key=lambda rect: rect[0])[1]
        rect_team3 = sorted(list(filter(lambda rect: math.fabs(rect[1] - y_max) < 10, rectangles)),
                            key=lambda rect: rect[0])[1]
        rect_team4 = sorted(list(filter(lambda rect: math.fabs(rect[1] - y_min) < 10, rectangles)),
                            key=lambda rect: rect[0])[0]
        rect_team5 = sorted(list(filter(lambda rect: math.fabs(rect[1] - y_max) < 10, rectangles)),
                            key=lambda rect: rect[0])[0]

        team1_position = Point(rect_team1[0], rect_team1[1], rect_team1[2], rect_team1[3])
        team2_position = Point(rect_team2[0], rect_team2[1], rect_team2[2], rect_team2[3])
        team3_position = Point(rect_team3[0], rect_team3[1], rect_team3[2], rect_team3[3])
        team4_position = Point(rect_team4[0], rect_team4[1], rect_team4[2], rect_team4[3])
        team5_position = Point(rect_team5[0], rect_team5[1], rect_team5[2], rect_team5[3])
        return [team1_position, team2_position, team3_position, team4_position, team5_position]
    return None


def get_start_btn_pre_fight(source_img):
    """
    Поиск кнопки "Начать" перед началом битвы
    :param source_img:
    :return: класс Point
    """
    test_show(source_img)
    color_from = (176, 114, 0)
    color_to = (186, 130, 6)
    mask = cv2.inRange(source_img, color_from, color_to)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.erode(mask, kernel, iterations=1)
    (centers, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rectangles = [cv2.boundingRect(x) for x in centers]
    btn_rect = max(rectangles, key=lambda x: x[2] * x[3])
    test_draw_rect(source_img, btn_rect)
    test_show(source_img)
    return Point(btn_rect[0], btn_rect[1], btn_rect[2], btn_rect[3])


def get_home_btn(source_img):
    """
    Возвращает позицию кнопки перехода в главное меню, которая находится в правом нижнем углу
    :param source_img:
    :return: Point
    """
    _, width, height = source_img.shape[::-1]
    gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 180, 250)
    circles = cv2.HoughCircles(canny,
                               cv2.HOUGH_GRADIENT,
                               1,
                               width / 8,
                               param1=100, param2=25,
                               minRadius=5, maxRadius=60)
    if circles is not None:
        circles = np.uint16(np.around(circles))
        if len(circles) == 1:
            center = (circles[0][0][0], circles[0][0][1])
            radius = circles[0][0][2]
            x = center[0] - radius
            y = center[1] - radius
            wh = radius * 2
            return Point(x, y, wh, wh)
    return None


def is_end_of_fight(source_img):
    _, width, height = source_img.shape[::-1]
    cropped_left = source_img[int(height * 0.8):height, 0:int(width * 0.4)]
    cropped_right = source_img[int(height * 0.8):height, int(width * 0.3):width]
    gray = cv2.cvtColor(cropped_right, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 170, 250)
    contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 1000, contours))
    filtered = []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        area = cv2.contourArea(contour)
        dif = math.fabs(rect[1][0]*rect[1][1] - area)
        if dif < 150:
            filtered.append(contour)
    contours = filtered
    if len(contours) < 3:
        return False
    contours = [cv2.boundingRect(item) for item in contours]
    contours.sort(key=lambda item: item[2] * item[3], reverse=True)
    max_area = max([item[2] * item[3] for item in contours])
    contours = list(filter(lambda item: math.fabs(item[2] * item[3] - max_area) < 1000, contours))
    contours.sort(key=lambda item: item[0])
    contours = list(set(contours))
    if len(contours) != 3:
        return False
    # filtered = []
    # for index in range(1, len(contours)):
    #     if math.fabs(contours[index - 1][0] - contours[index][0]) < 30:
    #         filtered.append(contours[index])
    # if len(filtered) != 3:
    #     return False

    # gray = cv2.cvtColor(cropped_left, cv2.COLOR_BGR2GRAY)
    # canny = cv2.Canny(gray, 170, 250)
    # contours, _ = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # circles = []
    # for contour in contours:
    #     approx = cv2.approxPolyDP(contour, 3, True)
    #     center, radius = cv2.minEnclosingCircle(approx)
    #     if radius < 10:
    #         continue
    #     center = (int(center[0]), int(center[1]))
    #     circles.append((center, radius))
    #
    # contours = [[circles[index]] for index in range(0, len(circles))]
    # for index in range(0, len(circles)):
    #     for index2 in range(0, len(circles)):
    #         if index == index2:
    #             continue
    #         distance = math.hypot(circles[index][0][0] - circles[index2][0][0],
    #                               circles[index][0][1] - circles[index2][0][1])
    #         if distance < circles[index][1] + circles[index2][1]:
    #             contours[index].append(circles[index2])
    # for index in range(0, len(circles)):
    #     for index2 in range(0, len(circles)):
    #         if index == index2:
    #             continue
    #         if len(list(set(contours[index]) & set(contours[index2]))) > 0:
    #             contours[index] = list(set(contours[index] + contours[index2]))
    #             contours[index2] = []
    # contours = list(filter(lambda item: len(item) > 0, contours))
    # if len(contours) == 3:
    #     return True
    # for contour in contours:
    #     max_circle = max(contour, key=lambda circle: circle[1])
    #     cv2.circle(cropped_left, max_circle[0], int(max_circle[1]), (0, 255, 0), 2)
    # test_show(cropped_left)
    return True


def get_end_fight_buttons(source_img):
    _, width, height = source_img.shape[::-1]
    cropped_right = source_img[int(height * 0.8):height, int(width * 0.3):width]
    gray = cv2.cvtColor(cropped_right, cv2.COLOR_BGR2GRAY)
    canny = cv2.Canny(gray, 170, 250)
    contours, _ = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda item: cv2.contourArea(item) > 100, contours))
    filtered = []
    for contour in contours:
        rect = cv2.minAreaRect(contour)
        area = cv2.contourArea(contour)
        dif = math.fabs(rect[1][0]*rect[1][1] - area)
        if dif < 150:
            filtered.append(contour)
    contours = filtered
    if len(contours) < 3:
        return False
    contours = [cv2.boundingRect(item) for item in contours]
    contours.sort(key=lambda item: item[2] * item[3], reverse=True)
    max_area = max([item[2] * item[3] for item in contours])
    contours = list(filter(lambda item: math.fabs(item[2] * item[3] - max_area) < 1000, contours))
    contours.sort(key=lambda item: item[0])
    contours = list(set(contours))
    if len(contours) != 3:
        return False
    # filtered = []
    # for index in range(1, len(contours)):
    #     if math.fabs(contours[index - 1][0] - contours[index][0]) < 30:
    #         filtered.append(contours[index])
    buttons_rect = [Point(rect[0] + int(width * 0.3),
                          rect[1] + int(height * 0.8),
                          rect[2],
                          rect[3])
                    for rect in contours]
    buttons_rect.sort(key=lambda item: item.x)
    return buttons_rect


def level_rectangles(img):
    _, width, height = img.shape[::-1]
    cropped = img[int(0.3 * height):int(0.5 * height), 0:width]
    _, width, height = cropped.shape[::-1]
    cropped = cv2.resize(cropped, (int(width * 1.5), int(height * 1.5)))
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda zip_item: zip_item[1][3] == -1, list(zip(contours, hierarchy[0]))))
    rects = [cv2.boundingRect(cnt[0]) for cnt in contours]
    rects = list(filter(lambda rect: rect[2] > rect[3] and rect[1] > 10, rects))
    rects = list(filter(lambda rect: rect[3] * 3 < rect[2] < rect[3] * 8, rects))
    rects = list(filter(lambda rect: rect[3] * rect[2] > 150, rects))
    rects.sort(key=lambda rect: rect[0])
    return rects


def text_leveling_from_image(img):
    _, width, height = img.shape[::-1]
    cropped = img[int(0.3*height):int(0.5*height), 0:width]
    _, width, height = cropped.shape[::-1]
    cropped = cv2.resize(cropped, (int(width*1.5), int(height*1.5)))
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda zip_item: zip_item[1][3] == -1, list(zip(contours, hierarchy[0]))))
    rects = [(cv2.boundingRect(cnt[0]), cnt[1]) for cnt in contours]
    rects = list(filter(lambda rect: rect[0][2] > rect[0][3] and rect[0][1] > 10, rects))
    rects = list(filter(lambda rect: rect[0][3] * 3 < rect[0][2] < rect[0][3] * 8, rects))
    max_rect = max(rects, key=lambda rect: rect[0][2] * rect[0][3])
    images = [thresh[rect[0][1]:rect[0][1]+rect[0][3], rect[0][0]:rect[0][0]+rect[0][2]] for rect in rects]
    images = [cv2.resize(image, (max_rect[0][2], max_rect[0][3])) for image in images]
    border_size = 10
    images = [cv2.copyMakeBorder(image, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT)
              for image in images]
    concat = cv2.vconcat(images)
    tesseract_path = os.getcwd() + '\\Tesseract-OCR'
    config_line = '--oem 1 --tessdata-dir "{}"'.format(tesseract_path + '\\tessdata')
    pytesseract.pytesseract.tesseract_cmd = tesseract_path + '\\tesseract.exe'
    data = pytesseract.image_to_data(concat,
                                     lang='rus_best',
                                     output_type=pytesseract.Output.DICT,
                                     config=config_line)
    zipped_data = list(zip(data['text'], data['left'], data['top'], data['width'], data['height']))
    zipped_data = list(filter(lambda item: item[0] != '', zipped_data))
    return zipped_data


def count_of_digits_energy(img):
    _, width, height = img.shape[::-1]
    cropped = img[:int(0.25*height), int(0.8*width):]
    _, width, height = cropped.shape[::-1]
    cropped = cv2.resize(cropped, (int(width*2), int(height*2)))
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    zipped = list(zip(hierarchy[0], contours))
    filtered = list(filter(lambda zip_item: zip_item[0][3] != -1, zipped))
    max_parent = max(itertools.groupby(filtered, key=lambda item: item[0][3]), key=lambda grp: len(list(grp[1])))
    childs = list(filter(lambda zip_item: zip_item[0][3] == max_parent[0], filtered))
    childs_rect = [cv2.boundingRect(child[1]) for child in childs]
    most_right = max(childs_rect, key=lambda rect: rect[0])
    most_left = min(childs_rect, key=lambda rect: rect[0])
    most_top = max(childs_rect, key=lambda rect: rect[1])
    most_height = max(childs_rect, key=lambda rect: rect[3])
    total_rect = [most_left[0] - 5,
                  most_top[1] - 5,
                  most_right[0] + most_right[2] - most_left[0] + 10,
                  most_height[3] + 5]
    energy_img = cropped[total_rect[1]:total_rect[1]+total_rect[3], total_rect[0]:total_rect[0]+total_rect[2]].copy()
    gray = cv2.cvtColor(energy_img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    thresh = cv2.erode(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contours)
    # childs_rect = [cv2.boundingRect(cnt) for cnt in contours]
    # childs_rect.sort(key=lambda rect: rect[0])
    # test_cells = []
    # border_size = 6
    # for rect in childs_rect:
    #     thresh_cell = thresh[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]].copy()
    #     # blank_image = np.zeros((thresh_cell.shape[0]+50, thresh_cell.shape[1]+50, 3), np.uint8)
    #     blank_image = cv2.copyMakeBorder(thresh_cell,
    #                                      border_size, border_size,
    #                                      border_size, border_size,
    #                                      cv2.BORDER_CONSTANT)
    #     blank_image = cv2.resize(blank_image, (20, 20))
    #     blank_image = blank_image.flatten()
    #     test_cells.append(blank_image)
    # test_cells = np.array(test_cells, dtype=np.float32)
    # # KNN
    # knn = cv2.ml.KNearest_load('digits_knearest.dat')
    # ret, result, neighbours, dist = knn.findNearest(test_cells, k=3)
    # print(result)
    # cv2.waitKey(0)
    # return None
