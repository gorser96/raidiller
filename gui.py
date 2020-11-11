from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt
from time import sleep
import game_module


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
        self.is_canceled = False
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
        self.campaign_resize_btn = QPushButton('Оптимальный размер окна')
        self.campaign_resize_btn.clicked.connect(self.on_click_campaign_resize_btn)
        self.campaign_repeat_btn = QPushButton('"Заново" и "Смена героев"')
        self.campaign_repeat_btn.clicked.connect(self.on_click_campaign_repeat_btn)
        self.campaign_repeat_label = QLabel('Координаты кнопки "Заново": ')
        self.campaign_max_energy_label = QLabel('Максимальное количество энергии:')
        self.campaign_max_energy_textbox = QLineEdit()
        self.campaign_max_energy_textbox.setValidator(QIntValidator(10, 200, self))
        self.campaign_is_cycled_checkbox = QCheckBox('До скончания времен')
        self.campaign_is_cycled_checkbox.setChecked(False)
        self.campaign_is_cycled_checkbox.setDisabled(True)
        self.campaign_is_cycled_checkbox.stateChanged.connect(self.state_changed_campaign_is_cycled_checkbox)
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
        self.campaign_cancel_btn = QPushButton('Отмена')
        self.campaign_cancel_btn.clicked.connect(self.on_click_cancel_btn)
        self.campaign_cancel_btn.setDisabled(True)

        self.tab_campaign.layout.addWidget(self.campaign_resize_btn)
        self.tab_campaign.layout.addWidget(self.campaign_repeat_btn)
        self.tab_campaign.layout.addWidget(self.campaign_repeat_label)
        self.tab_campaign.layout.addWidget(self.campaign_max_energy_label)
        self.tab_campaign.layout.addWidget(self.campaign_max_energy_textbox)
        self.tab_campaign.layout.addWidget(self.campaign_is_cycled_checkbox)
        self.tab_campaign.layout.addWidget(self.campaign_count_repeat_label)
        self.tab_campaign.layout.addWidget(self.campaign_count_repeat_textbox)
        self.tab_campaign.layout.addWidget(self.campaign_h_layout)
        self.tab_campaign.layout.addWidget(self.campaign_cancel_btn)
        self.tab_campaign.setLayout(self.tab_campaign.layout)
        self.campaign_worker = Worker(self.do_campaign_process)

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
        self.blind_repeat_worker = Worker(self.do_repeat_func)

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
        self.main_window_label.setText('Координаты окна игры: {} {}\n'
                                       'Размеры окна игры: {} {}'.format(wi.x, wi.y, wi.width, wi.height))

    def do_repeat_func(self):
        for index in range(0, self.repeats):
            self.parent().status_bar.showMessage('Номер боя: {}'.format(index + 1))
            game_module.click_repeat()
            sleep(2)
            game_module.wait_fighting()
        self.parent().status_bar.showMessage('Все бои завершены!')
        self.start_repeat_btn.setDisabled(False)

    def do_campaign_process(self):
        game_module.focus_raid()
        if self.campaign_is_cycled_checkbox.isChecked():
            max_energy = int(self.campaign_max_energy_textbox.text())
            index = 0
            while not self.is_canceled:
                try:
                    can_continue = game_module.is_enough_energy(max_energy)
                    print('enough of energy: {}'.format('yes' if can_continue else 'no'))
                    if can_continue:
                        need_update_heroes = game_module.is_need_change_heroes()
                        print('need update heroes: {}'.format('yes' if need_update_heroes else 'no'))
                        if need_update_heroes:
                            game_module.click_change()
                            # может выполниться миссия или испытание, которое помешает работе
                            sleep(6)
                            game_module.scroll_to_end_of_collection()
                            game_module.update_heroes()
                            sleep(2)
                            game_module.click_start_button()
                        else:
                            game_module.click_repeat()
                        self.parent().status_bar.showMessage('Номер боя: {}'.format(index + 1))
                        index = index + 1
                        sleep(2)
                        game_module.wait_fighting()
                        sleep(2)
                    else:
                        self.parent().status_bar.showMessage('Ожидание энергии')
                        # проверяем энергию раз в минуту, если накопилось 10 и более запускаем бой
                        sleep(60)
                except Exception as e:
                    self.parent().status_bar.showMessage(str(e))
                    continue
        else:
            for index in range(0, self.repeats):
                self.parent().status_bar.showMessage('Номер боя: {}'.format(index + 1))
                game_module.click_repeat()
                sleep(2)
                game_module.wait_fighting()
                if self.is_canceled:
                    break
            self.parent().status_bar.showMessage('Все бои завершены!')
            self.start_repeat_btn.setDisabled(False)

    def state_changed_campaign_is_cycled_checkbox(self, state):
        if state == Qt.Checked:
            self.campaign_count_repeat_label.setDisabled(True)
            self.campaign_count_repeat_textbox.setDisabled(True)
        else:
            self.campaign_count_repeat_label.setDisabled(False)
            self.campaign_count_repeat_textbox.setDisabled(False)

    @pyqtSlot()
    def on_click_campaign_resize_btn(self):
        game_module.resize_raid_window(1100, 750)

    @pyqtSlot()
    def on_click_cancel_btn(self):
        self.is_canceled = True
        self.campaign_cancel_btn.setDisabled(True)
        self.campaign_start_btn.setDisabled(False)
        self.campaign_resize_btn.setDisabled(False)
        self.campaign_test_btn.setDisabled(False)
        self.campaign_repeat_btn.setDisabled(False)
        self.campaign_is_cycled_checkbox.setDisabled(False)
        self.parent().status_bar.showMessage('Отмена')

    @pyqtSlot()
    def on_click_campaign_repeat_btn(self):
        QMessageBox.information(self,
                                'Help',
                                'Как выделить 2 кнопки:\n'
                                '1) Выделяем кнопку "Заново"\n'
                                '2) Нажимаем Enter\n'
                                '3) Выделяем кнопку "Смена героев"\n'
                                '4) Нажимаем Enter\n'
                                '5) Нажимаем Esc',
                                QMessageBox.Ok)
        game_module.focus_raid()
        points = game_module.init_rects_from_raid('Выделите кнопку "Заново" и "Смена героев"')
        if len(points) != 2:
            self.parent().status_bar.showMessage('Необходимо выделить 2 кнопки!')
            return
        if points[0].x < points[1].x:
            game_module.set_repeat_btn_position(points[0])
            game_module.set_change_btn_poistion(points[1])
            self.campaign_repeat_label.setText('Координаты кнопки "Заново": {} {}\n'
                                               'Координаты кнопки "Смена героев": {} {}'
                                               .format(points[0].x, points[0].y,
                                                       points[1].x, points[1].y))
        else:
            game_module.set_repeat_btn_position(points[1])
            game_module.set_change_btn_poistion(points[0])
        self.campaign_count_repeat_textbox.setDisabled(False)
        self.campaign_test_btn.setDisabled(False)
        self.campaign_start_btn.setDisabled(False)
        self.campaign_cancel_btn.setDisabled(False)
        self.campaign_is_cycled_checkbox.setDisabled(False)

    @pyqtSlot()
    def on_click_campaign_test_btn(self):
        game_module.focus_raid()
        need_change = game_module.is_need_change_heroes()
        QMessageBox.information(self,
                                'Test information',
                                'Is need change heroes?\n- {}'.format('yes' if need_change else 'no'),
                                QMessageBox.Ok)
        if self.campaign_max_energy_textbox.text() != '':
            max_energy = int(self.campaign_max_energy_textbox.text())
            is_enough_energy = game_module.is_enough_energy(max_energy)
            QMessageBox.information(self,
                                    'Test information',
                                    'Enough energy?\n- {}'.format('yes' if is_enough_energy else 'no'),
                                    QMessageBox.Ok)
    @pyqtSlot()
    def on_click_campaign_start_btn(self):
        self.is_canceled = False
        if not self.campaign_is_cycled_checkbox.isChecked():
            self.repeats = int(self.campaign_count_repeat_textbox.text())

        self.campaign_worker.start()

        self.campaign_cancel_btn.setDisabled(False)
        self.campaign_start_btn.setDisabled(True)
        self.campaign_resize_btn.setDisabled(True)
        self.campaign_test_btn.setDisabled(True)
        self.campaign_repeat_btn.setDisabled(True)
        self.campaign_is_cycled_checkbox.setDisabled(True)

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
