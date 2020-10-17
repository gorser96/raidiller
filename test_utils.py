import cv2


def test_show(source_img):
    cv2.imshow('test', source_img)
    cv2.waitKey(0)


def test_draw_rect(source_img, rect):
    x, y, w, h = rect
    cv2.rectangle(source_img, (x, y), (x + w, y + h), (0, 255, 0), 2)


def test_draw_point(source_img, point):
    test_draw_rect(source_img, (point.x, point.y, point.width, point.height))
