from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal
from time import sleep
import game_module
import enums


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('bot.ico'))
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(exit_action)

        self.status_bar = self.statusBar()

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Raidiller')

        self.workspace = Workspace(self)
        self.setCentralWidget(self.workspace)

        self.show()


class Workspace(QWidget):
    def __init__(self, parent):
        super(Workspace, self).__init__(parent)
        self.is_initialized = False
        self.repeats = 0
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)

        # вкладка "Главное"
        self.tab_main = QWidget()
        self.tab_main.layout = QVBoxLayout(self)
        self.main_init_btn = QPushButton('Поиск окна игры')
        self.main_init_btn.clicked.connect(self.on_click_main_init_btn)
        self.main_window_label = QLabel('Окно игры не найдено!')
        self.tab_main.layout.addWidget(self.main_init_btn)
        self.tab_main.layout.addWidget(self.main_window_label)
        self.tab_main.setLayout(self.tab_main.layout)

        # вкладка "Кампания"
        self.tab_campaign = QWidget()
        self.tab_campaign.layout = QVBoxLayout(self)
        self.campaign_repeat_btn = QPushButton('"Заново" и "Смена героев"')
        self.campaign_repeat_btn.clicked.connect(self.on_click_campaign_repeat_btn)
        self.campaign_collection_btn = QPushButton('Вырезать область "Коллекция героев"')
        self.campaign_collection_btn.clicked.connect(self.on_click_campaign_collection_btn)
        self.campaign_repeat_label = QLabel('Координаты кнопки "Заново": ')
        self.campaign_collection_label = QLabel('Координаты коллекции: ')
        self.campaign_count_repeat_label = QLabel('Количество повторов:')
        self.campaign_count_repeat_textbox = QLineEdit()
        self.campaign_count_repeat_textbox.setValidator(QIntValidator(0, 1000, self))
        self.campaign_count_repeat_textbox.setDisabled(True)
        self.campaign_h_layout = QWidget()
        self.campaign_h_layout.layout = QHBoxLayout(self)
        self.campaign_test_btn = QPushButton('Тест')
        self.campaign_test_btn.clicked.connect(self.on_click_campaign_test_btn)
        # self.campaign_test_btn.setDisabled(True)
        self.campaign_start_btn = QPushButton('Начать')
        self.campaign_start_btn.clicked.connect(self.on_click_campaign_start_btn)
        self.campaign_start_btn.setDisabled(True)
        self.campaign_h_layout.layout.addWidget(self.campaign_test_btn)
        self.campaign_h_layout.layout.addWidget(self.campaign_start_btn)
        self.campaign_h_layout.setLayout(self.campaign_h_layout.layout)
        self.tab_campaign.layout.addWidget(self.campaign_repeat_btn)
        self.tab_campaign.layout.addWidget(self.campaign_collection_btn)
        self.tab_campaign.layout.addWidget(self.campaign_repeat_label)
        self.tab_campaign.layout.addWidget(self.campaign_collection_label)
        self.tab_campaign.layout.addWidget(self.campaign_count_repeat_label)
        self.tab_campaign.layout.addWidget(self.campaign_count_repeat_textbox)
        self.tab_campaign.layout.addWidget(self.campaign_h_layout)
        self.tab_campaign.setLayout(self.tab_campaign.layout)

        # вкладка "Слепой повтор"
        self.tab_repeat = QWidget()
        self.tab_repeat.layout = QVBoxLayout(self)
        self.blind_extract_btn = QPushButton('Вырезать кнопку "Заново"')
        self.blind_extract_btn.clicked.connect(self.on_click_blind_extract_btn)
        self.blind_label_extracted = QLabel('Координаты кнопки "Заново": ')
        self.blind_label_repeat = QLabel('Количество повторов:')
        self.blind_count_repeat_textbox = QLineEdit()
        self.blind_count_repeat_textbox.setValidator(QIntValidator(0, 1000, self))
        self.blind_start_repeat_btn = QPushButton('Начать')
        self.blind_start_repeat_btn.clicked.connect(self.on_click_blind_start_repeat_btn)
        self.blind_count_repeat_textbox.setDisabled(True)
        self.blind_start_repeat_btn.setDisabled(True)
        self.tab_repeat.layout.addWidget(self.blind_extract_btn)
        self.tab_repeat.layout.addWidget(self.blind_label_extracted)
        self.tab_repeat.layout.addWidget(self.blind_label_repeat)
        self.tab_repeat.layout.addWidget(self.blind_count_repeat_textbox)
        self.tab_repeat.layout.addWidget(self.blind_start_repeat_btn)
        self.tab_repeat.setLayout(self.tab_repeat.layout)
        self.repeat_worker = Worker(self.do_repeat_func)

        # Добавление вкладок
        self.tabs.addTab(self.tab_main, "Главное")
        self.tabs.addTab(self.tab_campaign, "Кампания")
        self.tabs.addTab(self.tab_repeat, "Слепой повтор")
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click_main_init_btn(self):
        if not self.is_initialized:
            game_module.initialize()
            self.parent().status_bar.showMessage('Initialization completed!')
        self.is_initialized = True
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        self.tabs.setTabEnabled(3, True)
        wi = game_module.update_window_info()
        self.main_window_label.setText('Координаты окна игры: {} {}'.format(wi.x, wi.y))

    def do_repeat_func(self):
        for index in range(0, self.repeats):
            self.parent().status_bar.showMessage('Номер боя: {}'.format(index + 1))
            game_module.click_repeat()
            sleep(2)
            game_module.wait_fighting()
        self.parent().status_bar.showMessage('Все бои завершены!')
        self.start_repeat_btn.setDisabled(False)

    @pyqtSlot()
    def on_click_campaign_collection_btn(self):
        point = game_module.init_rect_from_raid('Выделите коллекцию героев')

    @pyqtSlot()
    def on_click_campaign_repeat_btn(self):
        game_module.focus_raid()
        points = game_module.init_rects_from_raid('Выделите кнопку "Заново" и "Смена героев"')
        if len(points) != 2:
            self.parent().status_bar.showMessage('Необходимо выделить 2 кнопки!')
            return
        if points[0].x < points[1].x:
            game_module.set_repeat_btn_position(points[0])
            game_module.set_change_btn_poistion(points[1])
            self.campaign_repeat_label.setText('Координаты кнопки "Заново": {} {}'.format(points[0].x, points[0].y))
        else:
            game_module.set_repeat_btn_position(points[1])
            game_module.set_change_btn_poistion(points[0])
        self.campaign_count_repeat_textbox.setDisabled(False)
        self.campaign_test_btn.setDisabled(False)
        self.campaign_start_btn.setDisabled(False)

    @pyqtSlot()
    def on_click_campaign_test_btn(self):
        game_module.focus_raid()
        team = game_module.get_team_icons()

    @pyqtSlot()
    def on_click_campaign_start_btn(self):
        point = game_module.init_rect_from_raid('Выделите кнопку "Заново"')

    @pyqtSlot()
    def on_click_blind_extract_btn(self):
        game_module.focus_raid()
        point = game_module.init_rect_from_raid('Выделите кнопку "Заново"')
        game_module.set_repeat_btn_position(point)
        self.blind_label_extracted.setText('Координаты кнопки "Заново": {} {}'.format(point.x, point.y))
        self.blind_count_repeat_textbox.setDisabled(False)
        self.blind_start_repeat_btn.setDisabled(False)

    @pyqtSlot()
    def on_click_blind_start_repeat_btn(self):
        self.repeats = int(self.blind_count_repeat_textbox.text())
        game_module.focus_raid()
        sleep(0.5)
        self.blind_start_repeat_btn.setDisabled(True)
        self.blind_repeat_worker.start()


class Worker(QThread):
    updateProgress = pyqtSignal(int)

    def __init__(self, func):
        QThread.__init__(self)
        self.func = func

    def __del__(self):
        try:
            if self.isRunning():
                self.wait()
        except RuntimeError:
            pass

    def run(self):
        self.func()
