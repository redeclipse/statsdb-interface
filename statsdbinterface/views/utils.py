# -*- coding: utf-8 -*-
import math


class Pages:

    def __init__(self, current, size, rows):
        self.current = current
        self.size = size
        self.rows = rows

    def total_pages(self):
        return math.ceil(self.rows / self.size)

    def last_page(self):
        return self.total_pages() - 1

    def previous(self):
        return max(0, self.current - 1)

    def next(self):
        return min(self.current + 1, self.last_page())

    def around(self, length):
        return range(max(0, self.current - length),
                     min(self.last_page(), self.current + 1 + length))
