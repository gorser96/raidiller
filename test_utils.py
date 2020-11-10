import cv2
from threading import Thread


def test_show(source_img):
    cv2.imshow('test', source_img)
    cv2.waitKey(0)


def test_draw_rect(source_img, rect):
    x, y, w, h = rect
    cv2.rectangle(source_img, (x, y), (x + w, y + h), (0, 255, 0), 2)


def test_draw_point(source_img, point):
    test_draw_rect(source_img, (point.x, point.y, point.width, point.height))


class TestThread(Thread):
    def __init__(self, func):
        """Инициализация потока"""
        Thread.__init__(self)
        self.do_process = func

    def run(self):
        """Запуск потока"""
        self.do_process()
