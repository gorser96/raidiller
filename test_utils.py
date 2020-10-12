import cv2


def test_show(source_img):
    cv2.imshow('test', source_img)
    cv2.waitKey(0)