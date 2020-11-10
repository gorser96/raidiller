# coding=utf-8
import win32gui
import cv2
from point import Point
from numpy import uint8, int32
from numpy.ma import array
from ctypes import windll
from time import sleep
from PIL import ImageGrab
from enums import RaidScreen
from easygui import *
from test_utils import test_show, test_draw_point, TestThread
from threading import Thread
import search_module
import pyautogui
import mouse
import random
import pickle
import os.path

__name_of_window = "Raid: Shadow Legends"
__config_file = 'config.pkl'
__location_file = 'loc_temp.png'
__repeat_btn_file = 'repeat_btn.png'
__border_height = 40
__window_info = None
__raid_hwnd = None
__current_screen = RaidScreen.MAIN_MENU
battle_position = None
campaign_position = None
dungeon_position = None
count_scroll = 0
location_position = None
location_template = None
level = 0
start_position = None
repeat_position = None
repeat_btn_template = None
change_position = None


def __save_config():
    global __window_info
    global battle_position
    global campaign_position
    global count_scroll
    global location_position
    global level
    global start_position
    global repeat_position
    global location_template
    global repeat_btn_template
    with open(__config_file, 'wb') as file:
        pickle.dump(__window_info, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(battle_position, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(campaign_position, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(count_scroll, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(location_position, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(level, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(start_position, file, pickle.HIGHEST_PROTOCOL)
        pickle.dump(repeat_position, file, pickle.HIGHEST_PROTOCOL)
        cv2.imwrite('sources\\{}'.format(__location_file), location_template)
        cv2.imwrite('sources\\{}'.format(__repeat_btn_file), repeat_btn_template)


def __load_config():
    global __window_info
    global battle_position
    global campaign_position
    global count_scroll
    global location_position
    global level
    global start_position
    global repeat_position
    global location_template
    global repeat_btn_template
    if os.path.exists(__config_file):
        with open(__config_file, 'rb') as file:
            __window_info = pickle.load(file)
            battle_position = pickle.load(file)
            campaign_position = pickle.load(file)
            count_scroll = pickle.load(file)
            location_position = pickle.load(file)
            level = pickle.load(file)
            start_position = pickle.load(file)
            repeat_position = pickle.load(file)
            location_template = cv2.imread('sources\\{}'.format(__location_file))
            repeat_btn_template = cv2.imread('sources\\{}'.format(__repeat_btn_file))


def __random_speed():
    return random.uniform(0.4, 1.8)


def __random_deviation(center):
    return random.uniform(center - 0.1, center + 0.1)


def __mouse_move(x, y, speed=None):
    mouse.move(__window_info.x + x,
               __window_info.y + y + __border_height,
               duration=__random_speed() if speed is None else speed)


def resize_raid_window(width, height):
    if __raid_hwnd:
        screen_width, screen_height = pyautogui.size()
        x = __window_info.x
        y = __window_info.y
        if x + width > screen_width:
            x = x + (screen_width - (x + width)) - 10
        if y + height > screen_height:
            y = y + (screen_height - (y + height)) - 10 - __border_height
        win32gui.MoveWindow(__raid_hwnd, x, y, width, height, True)
        __window_info.x = x
        __window_info.y = y
        __window_info.width = width
        __window_info.height = height


def __set_window_coordinates(hwnd, _):
    """
    Callback функция для перебора открытых окон, выполняет поиск окна игры
    """
    global __window_info
    global __raid_hwnd
    if win32gui.IsWindowVisible(hwnd):
        if __name_of_window in win32gui.GetWindowText(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            w = rect[2] - x
            h = rect[3] - y
            __window_info = Point(x, y, w, h)
            __raid_hwnd = hwnd


def __click_level():
    global level
    if level > 4:
        mouse.move(__window_info.center()[0],
                   __window_info.y + __window_info.height * 0.6,
                   duration=__random_speed())
        mouse.drag(__window_info.center()[0], __window_info.y + __window_info.height * 0.6,
                   __window_info.center()[0], __window_info.y + __window_info.height * 0.3,
                   duration=__random_speed())
    sleep(__random_speed())
    raid_screenshot = get_screen()
    position = search_module.get_level_position(raid_screenshot, level)
    btn_position = search_module.get_start_btn_from_level(raid_screenshot[position.y:position.y + position.height,
                                                          position.x:position.x + position.width])
    btn_position.x = position.x + btn_position.x
    btn_position.y = position.y + btn_position.y
    mouse.move(__window_info.x + btn_position.center()[0],
               __window_info.y + btn_position.center()[1] + __border_height,
               __random_speed())
    mouse.click()
    sleep(__random_deviation(0.5))


def focus_raid():
    win32gui.SetForegroundWindow(__raid_hwnd)
    sleep(__random_deviation(0.2))


def get_screen():
    """
    Получение скриншота окна игры
    """
    global __window_info
    box = (__window_info.x + 8,
           __window_info.y + __border_height,
           __window_info.x + __window_info.width - 8,
           __window_info.y + __window_info.height - 8)
    screen = ImageGrab.grab(box)
    img = array(screen.getdata(), dtype=uint8).reshape((screen.size[1], screen.size[0], 3))
    return img


def get_current_screen():
    raid_screenshot = get_screen()

    is_adv = search_module.is_ad(raid_screenshot)
    if is_adv:
        return RaidScreen.AD

    is_main = search_module.is_main_menu(raid_screenshot)
    if is_main:
        return RaidScreen.MAIN_MENU

    action_rectangles = search_module.get_actions_rectangles(raid_screenshot)
    if len(action_rectangles) > 2:
        return RaidScreen.ACTIONS

    _, width, height = raid_screenshot.shape[::-1]
    home_btn = search_module.get_home_btn(raid_screenshot[int(height * 0.8):height, int(width * 0.8):width])
    diff_btn = search_module.get_difficult_rectangle(raid_screenshot)
    if home_btn is not None and diff_btn is not None:
        return RaidScreen.CAMPAIGN

    is_lvl = search_module.is_level_selection(raid_screenshot)
    if is_lvl:
        return RaidScreen.CAMPAIGN_LEVEL

    is_pre_fight = search_module.is_pre_fight(raid_screenshot)
    if is_pre_fight:
        return RaidScreen.PRE_FIGHT

    raid_screenshot = get_screen()
    sleep(0.5)
    in_fight = search_module.is_fighting(raid_screenshot, get_screen())
    if in_fight:
        return RaidScreen.FIGHT

    end_fight = search_module.is_end_of_fight(raid_screenshot)
    if end_fight:
        return RaidScreen.END_FIGHT

    return RaidScreen.FATAL_TOWER


def go_main_actions():
    __mouse_move(battle_position.center()[0],
                 battle_position.center()[1])
    mouse.click()
    sleep(__random_speed())


def go_actions_campaign():
    __mouse_move(campaign_position.center()[0],
                 campaign_position.center()[1])
    mouse.click()
    sleep(__random_speed())


def go_scroll_location(scrolls):
    for index in range(0, scrolls):
        __mouse_move(__window_info.width * 0.9, __window_info.height * __random_deviation(0.5))
        mouse.drag(__window_info.width * 0.9, __window_info.height * __random_deviation(0.5),
                   __window_info.width * 0.1, __window_info.height * __random_deviation(0.5),
                   duration=__random_speed())
        sleep(__random_deviation(0.4))


def go_campaign_location():
    global count_scroll
    go_scroll_location(count_scroll)
    # raid_screenshot = get_screen()
    # temp_pos = search_module.get_object_position(raid_screenshot, location_template)
    __mouse_move(location_position.center()[0], location_position.center()[1])
    mouse.click()


def go_location_level():
    __click_level()


def click_start():
    __mouse_move(start_position.center()[0], start_position.center()[1])
    mouse.click()
    sleep(__random_speed())
    buttons = search_module.check_aura_at_start(get_screen())
    if buttons is not None:
        __mouse_move(buttons[1][0] + buttons[1][2] / 2,
                     buttons[1][1] + buttons[1][3] / 2)
        mouse.click()


def click_repeat_auto():
    buttons = search_module.get_end_fight_buttons(get_screen())
    repeat_btn = buttons[0]
    __mouse_move(repeat_btn.center()[0], repeat_btn.center()[1])
    mouse.click()


def click_repeat():
    __mouse_move(repeat_position.center()[0], repeat_position.center()[1])
    mouse.click()


def click_change():
    __mouse_move(change_position.center()[0], change_position.center()[1])
    mouse.click()


def wait_fighting():
    is_done = False
    while not is_done:
        frame1 = get_screen().copy()
        sleep(0.5)
        frame2 = get_screen().copy()
        if not search_module.is_fighting(frame1, frame2):
            is_done = True
        sleep(__random_deviation(0.5))
    sleep(__random_deviation(0.7))


def initialize():
    # отключение масштабирования экрана, для корректной работы с координатами
    user32 = windll.user32
    user32.SetProcessDPIAware()
    win32gui.EnumWindows(__set_window_coordinates, None)
    print('Detected raid window: {} {}'.format(__window_info.x, __window_info.y))
    # ожидание переключения окна
    sleep(0.2)


def update_window_info():
    global __raid_hwnd
    global __window_info
    if win32gui.IsWindowVisible(__raid_hwnd):
        rect = win32gui.GetWindowRect(__raid_hwnd)
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y
        __window_info = Point(x, y, w, h)
    return __window_info


def init_rects_from_raid(name):
    raid_screenshot = get_screen()
    from_center = False
    show_crosshair = False
    rects = cv2.selectROIs(name, raid_screenshot, fromCenter=from_center, showCrosshair=show_crosshair)
    points = [Point(rect[0], rect[1], rect[2], rect[3]) for rect in rects]
    cv2.destroyAllWindows()
    return points


def init_rect_from_raid(name):
    raid_screenshot = get_screen()
    from_center = False
    show_crosshair = False
    rect = cv2.selectROI(name,
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    rect_position = Point(rect[0], rect[1], rect[2], rect[3])
    cv2.destroyAllWindows()
    return rect_position


def configure():
    global battle_position
    global campaign_position
    global count_scroll
    global location_position
    global location_template
    global level
    global start_position
    global repeat_position
    global repeat_btn_template
    if os.path.exists(__config_file):
        choices = ["[<F1>]Да", "[<F2>]Нет"]
        result = ynbox('Найден файл конфигурации, загрузить?',
                       'Config',
                       choices=choices,
                       default_choice="[<F1>]Да",
                       cancel_choice="[<F2>]Нет")
        if result:
            __load_config()
            return

    msgbox('Откройте главное меню. \n'
           'После нажатия кнопки "Ок", выделите в кнопку "Бой" в появившемся окне. '
           'Для подтверждения выделения нажмите Enter',
           'Step 1',
           'OK')
    focus_raid()
    sleep(__random_speed())
    raid_screenshot = get_screen()
    from_center = False
    show_crosshair = False
    rect = cv2.selectROI('Выделите кнопку "Бой"',
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    battle_position = Point(rect[0], rect[1], rect[2], rect[3])
    cv2.destroyAllWindows()
    msgbox('Откройте меню "Бой". \n'
           'После нажатия кнопки "Ок", выделите баннер кампании в появившемся окне',
           'Step 2',
           'OK')
    focus_raid()
    sleep(__random_speed())
    raid_screenshot = get_screen()
    rect = cv2.selectROI('Выделите баннер кампании',
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    campaign_position = Point(rect[0], rect[1], rect[2], rect[3])
    cv2.destroyAllWindows()
    msgbox('Откройте карту кампании. \n'
           'После нажатия кнопки "Ок", введите количество необходимых прокруток карты, '
           'до нужной локации в кампании, в появившемся окне',
           'Step 3',
           'OK')
    focus_raid()
    sleep(__random_speed())

    values = enterbox('Количество необходимых прокруток карты', 'Ввод')
    count_scroll = int(values[0])

    msgbox('Выделите локацию. \n'
           'После нажатия кнопки "Ок", выделите нужную локацию в появившемся окне',
           'Step 4',
           'OK')
    focus_raid()
    sleep(__random_speed())
    raid_screenshot = get_screen()
    rect = cv2.selectROI('Выделите локацию',
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    location_position = Point(rect[0], rect[1], rect[2], rect[3])
    location_template = raid_screenshot[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]].copy()
    cv2.destroyAllWindows()
    msgbox('Введите номер уровня в локации. \n'
           'После нажатия кнопки "Ок", введите номер уровня в появившемся окне',
           'Step 5',
           'OK')
    focus_raid()
    sleep(__random_speed())

    values = enterbox('Номер уровня в локации', 'Ввод')
    level = int(values[0])

    msgbox('Выделите кнопку "Начать". \n'
           'Откройте окно выбора персонажей. '
           'После нажатия кнопки "Ок", выделите кнопку "Начать" в появившемся окне',
           'Step 6',
           'OK')
    focus_raid()
    sleep(__random_speed())
    raid_screenshot = get_screen()
    rect = cv2.selectROI('Выделите кнопку "Начать"',
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    start_position = Point(rect[0], rect[1], rect[2], rect[3])
    cv2.destroyAllWindows()
    focus_raid()
    msgbox('Выделите кнопку "Заново". \n'
           'Пройдите уровень в режиме Автобоя. '
           'После прохождения нажмите кнопку "Ок" и выделите кнопку "Заново" в появившемся окне',
           'Step 7',
           'OK')
    sleep(__random_speed())
    raid_screenshot = get_screen()
    rect = cv2.selectROI('Выделите кнопку "Заново"',
                         raid_screenshot,
                         fromCenter=from_center,
                         showCrosshair=show_crosshair)
    repeat_position = Point(rect[0], rect[1], rect[2], rect[3])
    repeat_btn_template = raid_screenshot[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]].copy()
    cv2.destroyAllWindows()
    __save_config()
    msgbox('Настройка пройдена успешно. \n'
           'Перейдите в главное меню. Вводите в консоль число (количество прохождений) для начала фарма.',
           'Finish',
           'OK')


def __func_feature():
    is_exit = False
    while not is_exit:
        raid_screenshot = get_screen()
        points = search_module.get_rect_features(raid_screenshot)
        for point in points:
            cv2.rectangle(raid_screenshot,
                          (point.x, point.y),
                          (point.x + point.width, point.y + point.height),
                          (0, 255, 0),
                          1)
        cv2.imshow('thread', raid_screenshot)
        cv2.waitKey(1)


def feature_thread():
    thread = TestThread(__func_feature)
    thread.start()


def auto_configure():
    global battle_position
    global __current_screen
    global dungeon_position
    global campaign_position
    global location_position
    global start_position
    global level

    sleep(__random_deviation(0.5))
    __current_screen = get_current_screen()
    if __current_screen != RaidScreen.MAIN_MENU:
        print('Please go to main menu and try again')
        return

    raid_screenshot = get_screen()
    _, width, height = raid_screenshot.shape[::-1]
    battle_loc = search_module.get_battle_btn(raid_screenshot[int(height * 0.7):height, int(width * 0.7):width])
    battle_position = Point(battle_loc[0] + int(width * 0.7),
                            battle_loc[1] + int(height * 0.7),
                            battle_loc[2], battle_loc[3])
    print('Found battle button')
    __mouse_move(battle_position.center()[0], battle_position.center()[1])
    mouse.click()
    sleep(__random_deviation(0.5))
    actions = search_module.get_actions_rectangles(get_screen())
    if actions is None:
        print('Error while searching for actions')
        return
    campaign_position = Point(actions[0][0], actions[0][1], actions[0][2], actions[0][3])
    dungeon_position = Point(actions[1][0], actions[1][1], actions[1][2], actions[1][3])
    print('Found actions')
    __mouse_move(campaign_position.center()[0], campaign_position.center()[1])
    mouse.click()
    sleep(__random_deviation(0.5))
    go_scroll_location(5)
    raid_screenshot = get_screen()
    location_avatars = search_module.get_rect_features(raid_screenshot)
    location_avatars = list(filter(lambda loc: loc.height > loc.width, location_avatars))
    location_position = location_avatars[-1]
    print('Found location position (sulfur trail)')
    __mouse_move(location_position.center()[0], location_position.center()[1])
    mouse.click()
    sleep(__random_deviation(0.5))
    level = 6
    __click_level()
    start_position = search_module.get_start_btn_pre_fight(get_screen())
    print('Found start button from pre fight screen')


def set_change_btn_poistion(point):
    global change_position
    change_position = point


def set_repeat_btn_position(point):
    global repeat_position
    repeat_position = point


def get_team_icons():
    raid_screenshot = get_screen()
    team = search_module.get_icon_teams(raid_screenshot)
    return team


class CollectionCheckThread(Thread):
    def __init__(self, template_pixel_tuple, top_rect_collection):
        """Инициализация потока"""
        Thread.__init__(self)
        self.template_pixel_tuple = template_pixel_tuple
        self.top_rect_collection = top_rect_collection

    def run(self):
        """Запуск потока"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        while True:
            raid_screenshot = get_screen()
            cropped = raid_screenshot[self.top_rect_collection:, :]
            mask = cv2.inRange(cropped, self.template_pixel_tuple, self.template_pixel_tuple)
            mask = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
            white_percent = len(mask[mask == 255]) / mask.size
            if white_percent > 0.35:
                break
            sleep(0.5)


def scroll_to_end_of_collection():
    raid_screenshot = get_screen()
    height, width, _ = raid_screenshot.shape
    template_pixel = raid_screenshot[height - 2, width - 2]
    template_pixel_tuple = uint8(template_pixel)
    top_rect_collection = 0
    for y in range(height - 2, 0, -1):
        if (raid_screenshot[y, width - 2] != template_pixel).any():
            top_rect_collection = y
            break
    cropped = raid_screenshot[top_rect_collection:height, :]
    mask = cv2.inRange(cropped, template_pixel_tuple, template_pixel_tuple)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cv2.boundingRect(cnt) for cnt in contours]
    most_right_cnt = max(contours, key=lambda cnt: cnt[0])
    x, y, w, h = most_right_cnt
    y = y + int(h / 2)
    x = x - 5
    while mask[y, x] == 255:
        x = x - 1
    y = top_rect_collection + int(cropped.shape[0] / 2)
    thr_check = CollectionCheckThread(template_pixel_tuple, top_rect_collection)
    thr_check.start()
    while thr_check.is_alive():
        mouse.move(__window_info.x + x - 20, __window_info.y + y + __border_height, duration=0.7)
        mouse.drag(__window_info.x + x - 20, __window_info.y + y + __border_height,
                   __window_info.x + 20, __window_info.y + y + __border_height,
                   duration=1.5)
    thr_check.join()
    sleep(0.5)


def update_heroes():
    raid_screenshot = get_screen()
    height, width, _ = raid_screenshot.shape
    pause = 0.2
    team = search_module.get_icon_teams(raid_screenshot)
    # убираем героев
    __mouse_move(team[1].center()[0], team[1].center()[1])
    mouse.click()
    sleep(pause)
    __mouse_move(team[2].center()[0], team[2].center()[1])
    mouse.click()
    sleep(pause)
    __mouse_move(team[3].center()[0], team[3].center()[1])
    mouse.click()
    sleep(pause)

    template_pixel = raid_screenshot[height - 2, width - 2]
    template_pixel_tuple = uint8(template_pixel)
    top_rect_collection = 0
    for y in range(height - 2, 0, -1):
        if (raid_screenshot[y, width - 2] != template_pixel).any():
            top_rect_collection = y
            break
    cropped = raid_screenshot[top_rect_collection:height, :]
    mask = cv2.inRange(cropped, template_pixel_tuple, template_pixel_tuple)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(cnt) for cnt in contours]
    most_right_cnt = max(boxes, key=lambda box: box[0])
    x, y, w, h = most_right_cnt
    y = y + int(h / 2)
    x = x - 5
    while mask[y, x] == 255:
        x = x - 1
    new_heroes = [Point(rect[0], rect[1] + top_rect_collection, rect[2], rect[3])
                  for rect in list(filter(lambda box: box[0] < x, boxes))]
    new_heroes.sort(key=lambda point: point.x, reverse=True)
    # добавляем новых героев
    __mouse_move(new_heroes[0].center()[0], new_heroes[0].center()[1])
    mouse.click()
    sleep(pause)
    __mouse_move(new_heroes[1].center()[0], new_heroes[1].center()[1])
    mouse.click()
    sleep(pause)
    __mouse_move(new_heroes[2].center()[0], new_heroes[2].center()[1])
    mouse.click()
    sleep(pause)


def click_start_button():
    raid_screenshot = get_screen()
    height, width, _ = raid_screenshot.shape
    template_pixel = raid_screenshot[height - 2, width - 2]
    template_pixel_tuple = uint8(template_pixel)
    top_rect_collection = 0
    for y in range(height - 2, 0, -1):
        if (raid_screenshot[y, width - 2] != template_pixel).any():
            top_rect_collection = y
            break
    cropped = raid_screenshot[top_rect_collection:height, :]
    mask = cv2.inRange(cropped, template_pixel_tuple, template_pixel_tuple)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.RETR_TREE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(cnt) for cnt in contours]
    boxes.sort(key=lambda box: box[0], reverse=True)
    if boxes[0][1] > boxes[1][1]:
        start_point = Point(boxes[0][0], boxes[0][1] + top_rect_collection, boxes[0][2], boxes[0][3])
    else:
        start_point = Point(boxes[1][0], boxes[1][1] + top_rect_collection, boxes[1][2], boxes[1][3])
    __mouse_move(start_point.center()[0], start_point.center()[1])
    mouse.click()


def is_need_change_heroes():
    raid_screenshot = get_screen()
    text_data = search_module.text_leveling_from_image(raid_screenshot)
    lines = [block[0].lower() for block in text_data]
    return len(list(filter(lambda line: 'макс' in line, lines))) > 1


def get_text_from_image():
    raid_screenshot = get_screen()
    return search_module.text_leveling_from_image(raid_screenshot)


def is_enough_energy(max_energy):
    count_of_digits_in_maximum = len(str(max_energy))
    raid_screenshot = get_screen()
    return search_module.count_of_digits_energy(raid_screenshot) - count_of_digits_in_maximum > 2

