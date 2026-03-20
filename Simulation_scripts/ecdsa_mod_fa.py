
from ecpy.curves import Curve
from sympy.ntheory.modular import crt
from sympy import factorint
from random import randrange, seed
import math
from collections import namedtuple
from tqdm import tqdm
from ecdl_reviewed import crack_baby_giant
import time
import json
from os.path import isfile

Entry = namedtuple("Entry", ("power", "m", "v"))

STUCK_00 = 0
STUCK_FF = 1
BIT_FLIP = 2

STALL_THRESHOLD = 100000

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

def faulty_signature(e, d, curve, fault_model):
    # Generate faulty modulus
    if fault_model == STUCK_FF:
        index = randrange(curve.size // 8)
        n = curve.order | (255 << (8 * index))
    elif fault_model == STUCK_00:
        index = randrange(curve.size // 8)
        n = curve.order - (curve.order & (255 << (8 * index)))
    elif fault_model == BIT_FLIP:
        index = randrange(curve.size)
        n = curve.order ^ (1 << index)
    else:
        raise ValueError("Invalid fault model")

    # Ensure k invertible mod n
    # while True:
    k = randrange(curve.order)
        # if math.gcd(k, n) == 1:
        #     break

    R = k * curve.generator
    r = int(R.x) % n
    s = (pow(k, -1, n) * (e + r * d)) % n

    return r, s, n, index, k


def get_small_factors(curve, B, fault_model):
    key = f"{curve.name}_{fault_model}_{B}"

    if not isfile("factors.json"):
        json_factors = {}
    else:
        with open("factors.json", "r") as f:
            json_factors = json.load(f)

    if key in json_factors:
        return json_factors[key]

    factors = set()

    indexes = curve.size if fault_model == BIT_FLIP else curve.size // 8

    for index in range(indexes):
        if fault_model == BIT_FLIP:
            faulty = curve.order ^ (1 << index)
        elif fault_model == STUCK_00:
            faulty = curve.order - (curve.order & (255 << (8 * index)))
        else:
            faulty = curve.order | (255 << (8 * index))

        factor_list = factorint(faulty, limit=B, use_rho=False, use_pm1=False, use_ecm=False)

        for p in factor_list.keys():
            if p < B:
                factors.add(p)

    json_factors[key] = list(factors)

    with open("factors.json", "w") as f:
        json.dump(json_factors, f, indent=2)

    return list(factors)


def attack(curve_name, fault_model, B, max_try, faulty_moduli_path=None):
    curve = Curve.get_curve(curve_name)
    external_faults = None
    if faulty_moduli_path is not None:
        external_faults = load_faulty_moduli(faulty_moduli_path)
        if not external_faults:
            raise ValueError("Empty faulty modulus list")
    sieve_list = get_small_factors(curve, B, fault_model)

    n = curve.order
    d = randrange(n)
    Q = d * curve.generator

    print(f"Correct key:   {d:X}")

    entries = {}

    returned_counter = 0
    used_counter = 0
    counter = 0
    last_used_counter = 0

    pbar = tqdm(total=curve.size)
    pbar_prev = 0

    while curve.size - pbar_prev > 40:
        if returned_counter - last_used_counter > STALL_THRESHOLD:
            return False, counter

        e = randrange(n)
        counter += 1

        try:
            if external_faults is not None:
                nf = external_faults[counter % len(external_faults)]

                # ensure k invertible mod nf
                # while True:
                k = randrange(curve.order)
                    # if math.gcd(k, nf) == 1:
                    #     break

                R = k * curve.generator
                r = int(R.x) % nf
                s = (pow(k, -1, nf) * (e + r * d)) % nf
            else:
                r, s, nf, _, _ = faulty_signature(e, d, curve, fault_model)
            returned_counter += 1

            used = False

            for p in sieve_list:
                if (p < B and s % p == 0 and r % p != 0 and nf % p == 0 and math.gcd(r, p) == 1):
                    a = 1
                    pa = p

                    while (s % pa == 0) and (r % pa != 0) and (nf % pa == 0):
                        pa *= p
                        a += 1

                    a -= 1
                    pa //= p

                    val = (-e * pow(r, -1, pa)) % pa

                    if p not in entries or entries[p].power < a:
                        if not used:
                            used_counter += 1
                            used = True
                            last_used_counter = returned_counter

                        entries[p] = Entry(a, val, pa)

            if entries:
                current_prod = math.prod(e.v for e in entries.values())
                current_log = math.log2(current_prod)

                delta = current_log - pbar_prev
                if delta > 0:
                    pbar.update(delta)
                    pbar_prev = current_log

        except ValueError:
            continue

    moduli = [e.v for e in entries.values()]
    residues = [e.m for e in entries.values()]

    dh = crt(moduli, residues)
    partial = dh[0]
    modulus = math.prod(moduli)

    if modulus >= curve.order:
        recovered = partial % curve.order
    else:
        print("\nSwitching to BSGS...")
        start = time.time()

        base = modulus * curve.generator
        target = Q - partial * curve.generator


        x = crack_baby_giant(curve, base, math.ceil(curve.order / modulus), target)
        recovered = x * modulus + partial

        print(f"BSGS time: {round(time.time() - start, 3)}s")

    pbar.close()

    print(f"Recovered key: {recovered:X}")
    print(f"Faults used:   {counter}")

    return recovered % curve.order == d, counter


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="ECDSA fault attack")

    parser.add_argument("--curve", default="secp256r1")
    parser.add_argument("--fault-model", type=int, default=STUCK_00)
    parser.add_argument("--B", type=int, default=2**12)
    parser.add_argument("--max-try", type=int, default=100000)
    parser.add_argument("--faulty-moduli", type=str, default=None,
                        help="Path to JSON list of faulty moduli")

    args = parser.parse_args()

    seed(1)

    key_found, counter = attack(
        args.curve,
        args.fault_model,
        args.B,
        args.max_try,
        faulty_moduli_path=args.faulty_moduli
    )