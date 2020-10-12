# coding=utf-8
import cv2
import numpy as np
from scipy.special.cython_special import ker

from point import Point
import math
from test_utils import test_show

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
    mask_close = __extract_color(source_img, (216, 206, 156))
    contours, _ = cv2.findContours(mask_close, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        # получение массива углов фигуры
        approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
        if len(approx) > 6:
            x, y, w, h = cv2.boundingRect(contour)
            # cv2.rectangle(source_img, (x, y), (x + w, y + h), (0, 255, 0), 2)


def is_main_menu(source_img):
    mask = __extract_color(source_img, (157, 152, 137))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(filter(lambda contour: cv2.contourArea(contour) > 200, contours))
    total_area = sum([cv2.contourArea(item) for item in contours])
    _, width, height = source_img.shape[::-1]
    cropped = source_img[int(height * 0.3):int(height * 0.6), 0:int(width * 0.1)]
    extracted = __extract_color(cropped, (16, 40, 50))
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
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


def is_fighting(source_img):
    _, width, height = source_img.shape[::-1]
    cropped = source_img[int(height * 0.6):height, 0:int(width * 0.3)]
    extracted = __extract_colors(cropped, (35, 0, 90), (60, 135, 117), cv2.COLOR_BGR2HSV)
    test_show(extracted)
    circles_bottom_corner = __get_circles(cropped)
    cv2.drawContours(cropped, circles_bottom_corner, -1, (0, 255, 0), 1)
    test_show(cropped)
    cropped = source_img[0:int(height * 0.2), int(width * 0.9):width]
    circles_top_corner = __get_circles(cropped)
    cv2.drawContours(cropped, circles_top_corner, -1, (0, 255, 0), 1)
    test_show(cropped)
    return 2 < len(circles_bottom_corner) < 5 and 0 < len(circles_top_corner) < 3


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


def get_level_position(source_img, level):
    color_from = (10, 70, 100)
    color_to = (20, 80, 110)
    extracted = __extract_colors(source_img, color_from, color_to)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
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
    color_from = (10, 70, 100)
    color_to = (20, 80, 110)
    extracted = __extract_colors(source_img, color_from, color_to)
    contours, _ = cv2.findContours(extracted, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rect_contours = [cv2.boundingRect(item) for item in contours]
    top_right_contour = max(rect_contours, key=lambda item: item[0])
    x, y, w, h = top_right_contour
    return Point(x, y, w, h)


def check_aura_at_start(source_img):
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


def __get_difficult_rectangle(source_img):
    """
    Выполняет поиск кнопки выбора уровня сложности в кампании
    :return: (x, y, width, height)
    """
    gray = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
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
