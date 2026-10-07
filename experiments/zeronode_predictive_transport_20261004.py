import random,statistics,json,time
from dataclasses import dataclass
@dataclass(frozen=True)
class S: e:int; r:int; h:int; m:int; hist:tuple
@dataclass(frozen=True)
class Q: e:int; r:int
def pi(s): return Q(s.e,s.r)
def pred(s): return (s.e*1315423911+s.r*2654435761)&((1<<64)-1)
def T(s):
 e=(s.e*17+3)&65535; r=(s.r^((s.e<<5)|(s.e>>11)))&65535
 return S(e,r,(s.h*1103515245+12345)&0xffffffff,(s.m+1+(r&3))&255,(s.hist+(s.h^s.m,))[-32:])
def Tb(q): return Q((q.e*17+3)&65535,(q.r^((q.e<<5)|(q.e>>11)))&65535)
def Z(s): return S(s.e,s.r,0,0,())
def it(f,x,n):
 for _ in range(n): x=f(x)
 return x
def run(seed,cases=2000,N=128):
 g=random.Random(seed); ok=[1]*5; red=[]
 for _ in range(cases):
  s=S(g.randrange(65536),g.randrange(65536),g.getrandbits(32),g.randrange(256),tuple(g.getrandbits(64) for _ in range(g.randrange(65))))
  q=pi(s); z=Z(s)
  ok[0] &= pi(z)==q and Z(z)==z
  ok[1] &= pred(z)==pred(s)
  ok[2] &= pi(T(s))==Tb(q)
  for n in range(N+1): ok[3] &= pi(it(T,s,n))==it(Tb,q,n)
  m=S(q.e,q.r,g.getrandbits(32),g.randrange(256),tuple(g.getrandbits(64) for _ in range(g.randrange(65))))
  ok[4] &= pi(m)==q and pred(m)==pred(s)
  red.append((len(repr(s)),len(repr(z))))
 return ok,statistics.mean(a-b for a,b in red)
t=time.perf_counter(); R=[run(i) for i in range(32)]
o={"protocol":"SIM2XR-ZN-PREDICTIVE-TRANSPORT-v1","seeds":32,"cases":64000,"recursive_depth":128,"recursive_checks":32*2000*129,"all_pass":all(all(x[0]) for x in R),"gates":["reconstruction","residual_zero","one_step_descent","recursive_descent","mutation_invariance"],"mean_bytes_eliminated":statistics.mean(x[1] for x in R),"elapsed_sec":time.perf_counter()-t}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["all_pass"] else 2)
