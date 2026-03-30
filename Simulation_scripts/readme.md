# Simulation Scripts

This folder contains scripts to simulate and optimize the "modulus fault attack" on ECDSA.

## Files

- `ecdsa_mod_fa_algo3.py`  
  Simulates faulty ECDSA signatures and performs private key recovery following Alg.3 from the article. 

- `ilp_solver.py`  
  Builds and solves an Integer Linear Programming (ILP) model to select optimal faults to perform. 

- `run_experiments.py`  
  Runs experiments to evaluate entropy vs. cost trade-offs for different attack settings.
  Supports external faulty moduli input (JSON) to assess practical faulty results.

- `ecdl_tool.py`
  Solves the ECDL with a simple python baby-step-giant-step implementation.

## Requirements

```bash
pip install ecpy sympy pulp
```

## Usage 

### Run attack simulation

  Simulates the attack described in Alg. 3 from the article.
  
  E.g.
```bash
python ecdsa_mod_fa_algo3.py --fault-model 00 --B 4096 --tau 216
[+] Target key: 1E2FEB89414C343C1027C4D1C386BBC4CD613E30D8F16ADF91B7584A2265B1F5
[+] Selected indices: [0, 1, 8, 11, 13, 15, 18, 19, 28]
[+] Expecting: 216.91391334051144 bits with 13028 faulty signatures
[+] Processing fault index 0
    [+] p=17
    [+] p=29
    [+] p=256
    [+] p=79
[+] Processing fault index 1
    [+] p=3
    [+] p=19
    [+] p=3319
    [+] p=617
[+] Processing fault index 8
    [+] p=23
    [+] p=353
[+] Processing fault index 11
    [+] p=2473
    [+] p=3637
[+] Processing fault index 13
    [+] p=11
    [+] p=73
    [+] p=167
    [+] p=313
    [+] p=421
    [+] p=1489
[+] Processing fault index 15
    [+] p=997
    [+] p=499
[+] Processing fault index 18
    [+] p=367
    [+] p=149
    [+] p=211
    [+] p=343
[+] Processing fault index 19
    [+] p=103
    [+] p=163
[+] Processing fault index 28
    [+] p=1097
    [+] p=2447
[+] Entropy reached: 216.91 > 216
Table built in 103.242s
[+] Recovered key: 1E2FEB89414C343C1027C4D1C386BBC4CD613E30D8F16ADF91B7584A2265B1F5
[+] Success: True
[+] Total number of signatures: 14856 (10760 used)
```
  N.B.
  - *When the inversion of the ephemeral key fails, the fault is considered unusable.*
  - *For practical ECDL on a standard laptop, the remaining entropy on the private key should not exceed 40 bits.* 

### Run optimization experiments

  Evaluates the cost in terms of fault to gain a certain amount of entropy on the private key.
  Can be used to replicate the simulations from Sect. 4 or to estimate the entropy gained with a given list of faulty moduli.

  E.g.

```bash
python run_experiments.py \
  --curve secp256r1 \
  --fault-type PFA \
  --fault-model ext \
  --B 65536 \
  --faulty-moduli faulty.json
Curve=secp256r1, model=ext, type=PFA, B=65536
[+] PFA -> H=  32 | faults=  1 | entropy=   39.83 | faulty sigs=63607
[+] PFA -> H=  64 | faults=  3 | entropy=   65.43 | faulty sigs=66083
[+] PFA -> H=  96 | faults=  5 | entropy=  103.13 | faulty sigs=97157
[+] PFA -> H= 128 | faults=  7 | entropy=  133.18 | faulty sigs=99239
[+] PFA -> H= 160 | faults= 10 | entropy=  165.78 | faulty sigs=100998
```

## Notes

- Fault models: 00 (STUCK_00), FF (STUCK_FF), bit flip (simulation only)

- Results are printed to stdout

