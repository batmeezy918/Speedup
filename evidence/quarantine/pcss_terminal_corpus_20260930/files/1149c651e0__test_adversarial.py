import struct
import hashlib

def run_sim(perturb_step=None, perturb_val=0.0):
    m, k, c, dt = 2.0, 5.0, 0.2, 0.02
    x, v = 0.5, 0.2
    full_hash = hashlib.sha256()
    
    for i in range(501):
        if perturb_step is not None and i == perturb_step:
            x += perturb_val # Inject Delta
            
        t = i * dt
        a = -(k * x + c * v) / m
        E = 0.5 * k * x * x + 0.5 * m * v * v
        
        record = struct.pack('>d', t) + struct.pack('>d', x) + \
                 struct.pack('>d', v) + struct.pack('>d', a) + \
                 struct.pack('>d', E)
        full_hash.update(record)
        
        v_new = v + a * dt
        x_new = x + v * dt
        v = v_new
        x = x_new
        
    return full_hash.hexdigest()

print("ADVERSARIAL_TEST_START")
# Baseline
h1 = run_sim()
h2 = run_sim() # Run twice to prove determinism

# Perturbed (Delta = 1e-15 at step 250)
h_perturb_1 = run_sim(perturb_step=250, perturb_val=1e-15)
h_perturb_2 = run_sim(perturb_step=250, perturb_val=1e-15)

print(f"BASELINE_RUN_1|{h1}")
print(f"BASELINE_RUN_2|{h2}")
print(f"PERTURBED_RUN_1|{h_perturb_1}")
print(f"PERTURBED_RUN_2|{h_perturb_2}")
print("ADVERSARIAL_TEST_END")
