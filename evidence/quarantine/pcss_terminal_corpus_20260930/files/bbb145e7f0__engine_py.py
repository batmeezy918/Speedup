import json
import struct
import hashlib

with open('spec.json') as f:
    spec = json.load(f)

m, k, c, dt = spec['mass'], spec['k'], spec['c'], spec['dt']
x, v = spec['x0'], spec['v0']
steps = spec['steps']

def to_hex(val):
    # Exact IEEE 754 binary64 raw memory representation
    return struct.pack('>d', val).hex()

trajectory_hashes = []
full_hash = hashlib.sha256()

# Checkpoints to record
checkpoints = {0, 1, 2, 10, 100, 250, 500}

print(f"PYTHON_EXEC_START")
for i in range(steps + 1):
    t = i * dt
    a = -(k * x + c * v) / m
    E = 0.5 * k * x * x + 0.5 * m * v * v
    
    if i in checkpoints:
        print(f"CHK_{i}|t={to_hex(t)}|x={to_hex(x)}|v={to_hex(v)}|a={to_hex(a)}|E={to_hex(E)}")
    
    # Canonical byte sequence for hashing
    record = f"{to_hex(t)}{to_hex(x)}{to_hex(v)}{to_hex(a)}{to_hex(E)}".encode('utf-8')
    full_hash.update(record)
    
    # Advance state (Strict ordering: use old v for new x)
    v_new = v + a * dt
    x_new = x + v * dt
    v = v_new
    x = x_new

print(f"FULL_HASH|{full_hash.hexdigest()}")
print(f"PYTHON_EXEC_END")
