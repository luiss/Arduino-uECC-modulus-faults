import time
from math import ceil, sqrt

baby_table = {}
baby_table2 = {}


def crack_baby_giant(curve, P, n, Q, m=0):
    baby_table.clear()
    baby_table2.clear()

    start_time = time.time()

    if m == 0:
        m = int(ceil(sqrt(n)))

    bP = P
    for b in range(1, m):
        baby_table[bP.x] = b
        bP = bP + P

    print(f"Table built in {round(time.time() - start_time, 3)}s")

    M = m * P
    R = Q

    for g in range(int(n / m) + 1):
        if R.x in baby_table:
            return baby_table[R.x] + g * m
        R = R - M

    return None