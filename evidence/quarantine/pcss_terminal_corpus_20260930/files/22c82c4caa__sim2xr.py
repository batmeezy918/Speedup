import struct
import hashlib
import sys

M = float(2.0)
K = float(5.0)
C = float(0.2)
DT = float(0.02)

X0 = float(0.5)
V0 = float(0.2)

STEPS = 500

def acceleration(x, v):
    p1 = K * x
    p2 = C * v
    s1 = p1 + p2
    q1 = s1 / M
    a1 = -q1
    return a1

def energy(x, v):
    h = float(0.5)

    p1 = h * K
    p2 = p1 * x
    p3 = p2 * x

    q1 = h * M
    q2 = q1 * v
    q3 = q2 * v

    e = p3 + q3
    return e

def record(buf, i, t, x, v, a, e):
    buf.extend(struct.pack(">Q", i))
    buf.extend(struct.pack(">d", t))
    buf.extend(struct.pack(">d", x))
    buf.extend(struct.pack(">d", v))
    buf.extend(struct.pack(">d", a))
    buf.extend(struct.pack(">d", e))

def run(perturb_step=-1, perturb_value=0.0):
    buf = bytearray()
    checkpoints = {}

    x = X0
    v = V0

    for i in range(STEPS + 1):

        if i == perturb_step:
            x = x + perturb_value

        ii = float(i)
        t = ii * DT

        a = acceleration(x, v)
        e = energy(x, v)

        record(buf, i, t, x, v, a, e)

        if i in (0,1,2,10,100,250,500):
            checkpoints[i] = (
                struct.pack(">d", t).hex(),
                struct.pack(">d", x).hex(),
                struct.pack(">d", v).hex(),
                struct.pack(">d", a).hex(),
                struct.pack(">d", e).hex(),
            )

        if i < STEPS:
            a_prev = a

            av = a_prev * DT
            v_new = v + av

            xv = v * DT
            x_new = x + xv

            v = v_new
            x = x_new

    if len(buf) != 24048:
        raise RuntimeError(
            "CANONICAL SIZE FAILURE: "
            + str(len(buf))
            + " != 24048"
        )

    return bytes(buf), hashlib.sha256(buf).hexdigest(), checkpoints

base, bh, bc = run()
base2, bh2, bc2 = run()

pert, ph, pc = run(250, float(1e-15))
pert2, ph2, pc2 = run(250, float(1e-15))

open("python_baseline.bin","wb").write(base)
open("python_perturbed.bin","wb").write(pert)

print("PYTHON")
print("SIZE=",len(base))
print("HASH=",bh)
print("REPLAY_BYTES=",base == base2)
print("REPLAY_HASH=",bh == bh2)
print("PERTURBED_HASH=",ph)
print("PERTURBED_REPLAY=",pert == pert2 and ph == ph2)
print("PERTURBATION_CHANGED=",bh != ph)
print("STATE250_CHANGED=",bc[250][1] != pc[250][1])

for i in (0,1,2,10,100,250,500):
    print(
        "CHK",i,
        *bc[i]
    )
