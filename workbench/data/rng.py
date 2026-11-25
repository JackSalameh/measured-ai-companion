"""Portable random helpers built only on random.random(), whose output for an integer seed
Python guarantees not to change across versions. Other random-module methods may change."""
import math
import random


class Rng:
    def __init__(self, seed):
        self.r = random.Random(seed)

    def uniform(self, a=0.0, b=1.0):
        return a + (b - a) * self.r.random()

    def normal(self, mu=0.0, sd=1.0):  # Box-Muller
        u1, u2 = 1.0 - self.r.random(), self.r.random()
        return mu + sd * math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

    def index(self, n):
        return min(int(self.r.random() * n), n - 1)

    def choice(self, seq):
        return seq[self.index(len(seq))]

    def weighted(self, items, weights):
        x, acc = self.r.random() * sum(weights), 0.0
        for it, w in zip(items, weights):
            acc += w
            if x < acc:
                return it
        return items[-1]

    def chance(self, p):
        return self.r.random() < p
