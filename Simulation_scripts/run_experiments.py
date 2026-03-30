import argparse
from ecpy.curves import Curve

from ilp_solver import *


def main():
    parser = argparse.ArgumentParser(description="Fault attack optimization via ILP")
    parser.add_argument("--curve", required=True, help="Curve name (e.g., secp256r1)")
    parser.add_argument("--fault-type", choices=["PFA", "TFA"], required=True,
                        help="PFA (persistent) or TFA (transient)")
    parser.add_argument("--fault-model", choices=["00", "FF", "ext"], required=True,
                        help="Fault model: 00 (STUCK_00) or FF (STUCK_FF)")
    parser.add_argument("--B", type=int, required=True,
                        help="Factor bound (e.g., 4096)")
    parser.add_argument("--delta", type=int, default=10,
                        help="Entropy slack Delta (default: 10)")
    parser.add_argument("--min-entropy", type=int, default=32,
                        help="Minimum target entropy (default: 32)")
    parser.add_argument("--max-entropy", type=int, default=None,
                        help="Maximum target entropy (default: curve size)")
    parser.add_argument("--step", type=int, default=32,
                        help="Entropy step (default: 32)")
    parser.add_argument("--faulty-moduli", type=str, default=None,
                        help="Path to JSON list of faulty moduli")


    args = parser.parse_args()

    curve = Curve.get_curve(args.curve)

    fault_type = PERSISTENT if args.fault_type == "PFA" else TRANSIENT
    fault_model = STUCK_00 if args.fault_model == "00" else STUCK_FF

    max_entropy = args.max_entropy if args.max_entropy is not None else curve.size

    print(f"Curve={args.curve}, model={args.fault_model}, type={args.fault_type}, B={args.B}")

    lists = build_factor_lists(curve, fault_model, args.B, faulty_moduli_path=args.faulty_moduli)

    if not lists:
        print("No usable factor lists generated.")
        return

    for target_entropy in range(args.min_entropy, max_entropy + args.step, args.step):

        if fault_type == PERSISTENT:
            res = solve_for_pfa(lists, target_entropy, args.delta)
            if res:
                print(f"[+] PFA -> H={target_entropy:4d} | faults={len(res[0]):3d} | entropy={res[2]:8.2f} | faulty sigs={res[3]}")
        else:
            res = solve_for_tfa(lists, target_entropy, args.delta)
            if res:
                print(f"[+] TFA -> H={target_entropy:4d} | cost={res[3]:8d} | entropy={res[2]:8.2f}")

if __name__ == "__main__":
    main()