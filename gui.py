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
        self.init_btn = QPushButton('Поиск окна игры')
        self.init_btn.clicked.connect(self.on_click_init_btn)
        self.window_label = QLabel('Окно игры не найдено!')
        self.tab_main.layout.addWidget(self.init_btn)
        self.tab_main.layout.addWidget(self.window_label)
        self.tab_main.setLayout(self.tab_main.layout)

        # вкладка "Кампания"
        # self.tab_campaign = QWidget()

        # вкладка "Слепой повтор"
        self.tab_repeat = QWidget()
        self.tab_repeat.layout = QVBoxLayout(self)
        self.label_repeat = QLabel('Количество повторов:')
        self.count_repeat_textbox = QLineEdit()
        self.count_repeat_textbox.setValidator(QIntValidator(0, 1000, self))
        self.start_repeat_btn = QPushButton('Начать')
        self.start_repeat_btn.clicked.connect(self.on_click_start_repeat_btn)
        self.tab_repeat.layout.addWidget(self.label_repeat)
        self.tab_repeat.layout.addWidget(self.count_repeat_textbox)
        self.tab_repeat.layout.addWidget(self.start_repeat_btn)
        self.tab_repeat.setLayout(self.tab_repeat.layout)
        self.repeat_worker = Worker(self.do_repeat_func)

        # Добавление вкладок
        self.tabs.addTab(self.tab_main, "Главное")
        # self.tabs.addTab(self.tab_campaign, "Кампания")
        self.tabs.addTab(self.tab_repeat, "Слепой повтор")
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    @pyqtSlot()
    def on_click_init_btn(self):
        if not self.is_initialized:
            game_module.initialize()
            self.parent().status_bar.showMessage('Initialization completed!')
        self.is_initialized = True
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        wi = game_module.update_window_info()
        self.window_label.setText('Координаты окна игры: {} {}'.format(wi.x, wi.y))

    def do_repeat_func(self):
        for index in range(0, self.repeats):
            self.parent().status_bar.showMessage('Номер боя: {}'.format(index + 1))
            game_module.click_repeat_auto()
            sleep(2)
            game_module.wait_fighting()
        self.parent().status_bar.showMessage('Все бои завершены!')
        self.start_repeat_btn.setDisabled(False)

    @pyqtSlot()
    def on_click_start_repeat_btn(self):
        self.repeats = int(self.count_repeat_textbox.text())
        game_module.focus_raid()
        sleep(0.5)
        if game_module.get_current_screen() != enums.RaidScreen.END_FIGHT:
            self.parent().status_bar.showMessage('Ошибка, необходимо быть на экране конца боя!')
            return
        self.start_repeat_btn.setDisabled(True)
        self.repeat_worker.start()


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
