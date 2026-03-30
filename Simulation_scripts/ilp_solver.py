from sympy import factorint
import math
import pulp
from collections import defaultdict

STUCK_00 = "00"
STUCK_FF = "FF"
PERSISTENT = 0
TRANSIENT = 1

def _build_problem(lists, B, Delta, minimize_cost=False):
    n = len(lists)
    prob = pulp.LpProblem("PrimeExponentCover", pulp.LpMinimize)

    # Decision variables
    x = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(n)]

    # Precompute costs safely
    cost = []
    for d in lists:
        if d:
            cost.append(max(p ** k for p, k in d.items()))
        else:
            cost.append(0)

    # Collect primes and exponents
    primes = defaultdict(set)
    for d in lists:
        for p, k in d.items():
            if p > 1:  # ignore dummy factor
                primes[p].add(k)

    # Variables y[p,k]
    y = {}
    for p, ks in primes.items():
        for k in ks:
            y[(p, k)] = pulp.LpVariable(f"y_{p}_{k}", cat="Binary")

    # Objective
    if minimize_cost:
        prob += pulp.lpSum(cost[i] * x[i] for i in range(n))
    else:
        prob += pulp.lpSum(x[i] for i in range(n))

    # One exponent per prime
    for p, ks in primes.items():
        prob += pulp.lpSum(y[(p, k)] for k in ks) <= 1

    # Link y and x
    for (p, k), var in y.items():
        prob += var <= pulp.lpSum(
            x[i] for i in range(n) if lists[i].get(p, 0) == k
        )

    # Entropy gain
    G = pulp.lpSum(k * math.log2(p) * y[(p, k)] for (p, k) in y)

    prob += G >= B
    prob += G <= B + Delta

    return prob, x, y, cost

def solve_for_pfa(lists, B, Delta):
    prob, x, y, cost = _build_problem(lists, B, Delta, minimize_cost=False)
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[status] != "Optimal":
        return None

    return _extract_solution(lists, x, y, cost)

def solve_for_tfa(lists, B, Delta):
    prob, x, y, cost = _build_problem(lists, B, Delta, minimize_cost=True)
    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[status] != "Optimal":
        return None

    return _extract_solution(lists, x, y, cost)

def _extract_solution(lists, x, y, cost):
    # Selected exponents
    expo = {}
    for (p, k), var in y.items():
        if pulp.value(var) > 0.5:
            expo[p] = k

    sol_lists = []
    for i in range(len(lists)):
        if pulp.value(x[i]) > 0.5:
            sol_lists.append(i)

    # Recompute effective cost more cleanly
    effective_cost = 0
    for i in sol_lists:
        relevant = [p ** expo[p] for p in lists[i] if p in expo]
        if relevant:
            effective_cost += max(relevant)

    G_val = sum(k * math.log2(p) for p, k in expo.items())

    return sol_lists, expo, G_val, effective_cost

def load_faulty_moduli(path):
    import json

    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Faulty modulus file must contain a list")

    moduli = []
    for x in data:
        if not isinstance(x, str):
            raise ValueError("All entries must be hex strings")

        x = x.lower().strip()
        if x.startswith("0x"):
            x = x[2:]

        moduli.append(int(x, 16))

    return moduli

def build_factor_lists(curve, fault_model, B, faulty_moduli_path=None):
    lists = []
    faulties = None
    if faulty_moduli_path is not None:
        faulties = load_faulty_moduli(faulty_moduli_path)
        if not faulties:
            raise ValueError("Empty faulty modulus list")
    else:
        faulties = list()
        indexes = curve.size // 8
        for index in range(indexes):
            if fault_model == STUCK_00:
                faulty = curve.order - (curve.order & (255 << (8 * index)))
            elif fault_model == STUCK_FF:
                faulty = curve.order | (255 << (8 * index))
            else:
                raise ValueError("Unsupported fault model")
            faulties.append(faulty)

    for faulty in faulties:
        factor_list = factorint(
            faulty,
            limit=B,
            use_rho=False,
            use_pm1=False,
            use_ecm=False,
        )

        # Keep only small factors
        filtered = {p: k for p, k in factor_list.items() if p <= B}

        if filtered:
            lists.append(filtered)
        else:
            lists.append({1:1})

    return lists
