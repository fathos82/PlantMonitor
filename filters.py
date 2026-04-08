from abc import ABC
from typing import Any, List


class Filter(ABC):

    def filter(self, data:float) -> float:
        pass

class KalmanFilter1D(Filter):
    def __init__(self, q=0.01, r=20, x0=0.0):
        self.q = q    # ruído do processo
        self.r = r    # ruído da medição
        self.p = 1.0  # incerteza estimada
        self.x = x0   # valor filtrado atual

    def filter(self, z):
        self.p += self.q
        k = self.p / (self.p + self.r)
        self.x += k * (z - self.x)
        self.p *= (1 - k)
        return self.x