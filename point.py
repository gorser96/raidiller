class Point:
    x = 0
    y = 0
    width = 0
    height = 0

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def top(self):
        return self.x, self.y

    def bottom(self):
        return self.x + self.width, self.y + self.height
