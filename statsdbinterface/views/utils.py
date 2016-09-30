# -*- coding: utf-8 -*-
import math


class Pages:

    def __init__(self, current, size, rows):
        self.current = current
        self.size = size
        self.rows = rows

    def total_pages(self):
        return math.ceil(self.rows / self.size)
