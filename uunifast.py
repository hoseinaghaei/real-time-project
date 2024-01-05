import random


def generate_uunifast_discard(u: float, n: int):
    sets = []
    while len(sets) < 1:
        utilization = []
        sum_utilization = u
        for i in range(1, n):
            next_sum_utilization = sum_utilization * random.random() ** (1.0 / (n - i))
            utilization.append(sum_utilization - next_sum_utilization)
            sum_utilization = next_sum_utilization
        utilization.append(sum_utilization)

        if all(ut <= 1 for ut in utilization):
            return utilization
