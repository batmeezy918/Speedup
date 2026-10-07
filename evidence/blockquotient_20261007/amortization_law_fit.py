import subprocess, re, collections, math
out = subprocess.run(["./agd_amortized_total"], capture_output=True, text=True, timeout=2400).stdout
rows=[]
for l in out.splitlines():
    m=re.match(r"AMORTIZED d=(\d+) tile=(\d+) r=(\d+) steps=(\d+) total_speedup=([\d.]+)x setup_included=YES maxerr=(\S+)", l)
    if m:
        rows.append(dict(d=int(m.group(1)),tile=int(m.group(2)),r=int(m.group(3)),steps=int(m.group(4)),
                         sp=float(m.group(5)),maxerr=m.group(6)))
print(f"parsed {len(rows)} rows;  all maxerr==0: {all(r['maxerr']=='0' for r in rows)}")
print()
print("MODEL  1/E2E(k) = a/k + b      =>  E2E(k) = 1/(a/k+b)")
print("  a = C_fixed / C_full      (one-time overhead, amortised)")
print("  b = C_quot / C_full      (asymptotic per-step ratio)")
print()
print(f"{'d':>6} {'tile':>4} {'r':>5} | {'a=Cfix/Cf':>10} {'b=Cq/Cf':>9} {'asymptote':>10} {'k_break':>8} {'fit R2':>7} | {'E2E(1)':>8} {'E2E(64)':>9}")
for (d,tile) in sorted({(r['d'],r['tile']) for r in rows}):
    g=sorted([r for r in rows if r['d']==d and r['tile']==tile], key=lambda r:r['steps'])
    ks=[r['steps'] for r in g]; ys=[1.0/r['sp'] for r in g]
    n=len(ks); sx=sum(1/k for k in ks); sy=sum(ys)
    sxx=sum(1/k*1/k for k in ks); sxy=sum(1/k*y for k,y in zip(ks,ys))
    den=n*sxx-sx*sx
    a=(n*sxy-sx*sy)/den; b=(sy-a*sx)/n
    ybar=sy/n
    ss_tot=sum((y-ybar)**2 for y in ys); ss_res=sum((y-(a/k+b))**2 for k,y in zip(ks,ys))
    r2=1-ss_res/ss_tot if ss_tot>0 else float('nan')
    asymp=1/b
    kbreak=a/(1-b) if b<1 else float('inf')
    def pred(k): return 1.0/(a/k+b)
    print(f"{d:>6} {tile:>4} {g[0]['r']:>5} | {a:>10.5f} {b:>9.6f} {asymp:>9.1f}x {kbreak:>8.3f} {r2:>7.4f} | {pred(1):>7.1f}x {pred(64):>8.1f}x")
print()
print("PREDICTION CHECK: does 1/E2E linear in 1/k hold?  (R2 column)")
print("  If R2 ~ 1, the amortization model E2E(k)=1/(a/k+b) is validated on this device,")
print("  and the break-even k is read off directly rather than assumed.")
