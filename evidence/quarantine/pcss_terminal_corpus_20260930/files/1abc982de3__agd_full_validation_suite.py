import time
import random
from collections import deque


# ============================================================
# AGD FULL VALIDATION SUITE
# ============================================================


N_VALUES = [
    100000,
    1000000,
    5000000
]


BUCKET = 5000


# ------------------------------------------------------------
# Transition operators
# ------------------------------------------------------------

def linear_T(x,N):

    if x+1 < N:
        yield x+1



def nonlinear_T(x,N):

    moves=[
        x+1,
        x+7,
        x*2+1,
        x//2
    ]

    for y in moves:

        if 0 <= y < N:
            yield y



# ------------------------------------------------------------
# BFS
# ------------------------------------------------------------

def bfs(N,T,limit=1000000):

    start=0
    goal=N-1

    q=deque([start])

    visited={start}

    count=0


    while q:

        x=q.popleft()

        count+=1


        if x==goal:
            return True,count


        if count>=limit:
            return False,count


        for y in T(x,N):

            if y not in visited:

                visited.add(y)

                q.append(y)


    return False,count



# ------------------------------------------------------------
# Quotient
# ------------------------------------------------------------

def Q(x):

    return x//BUCKET



def signature(x,N,T):

    return tuple(
        sorted(
            Q(y)
            for y in T(x,N)
        )
    )



def valid_class(c,N,T):

    a=c*BUCKET
    b=min(a+BUCKET,N)

    ref=None


    for x in range(a,b):

        s=signature(x,N,T)


        if ref is None:

            ref=s


        elif s!=ref:

            return False


    return True



def quotient(N,T):

    start=Q(0)

    goal=Q(N-1)


    q=deque([start])

    visited={start}

    count=0


    while q:

        c=q.popleft()

        count+=1


        if c==goal:

            return True,count



        if not valid_class(c,N,T):

            continue



        a=c*BUCKET

        b=min(a+BUCKET,N)


        for x in range(a,b):

            for y in T(x,N):

                yc=Q(y)

                if yc not in visited:

                    visited.add(yc)

                    q.append(yc)



    return False,count



# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------


print("="*70)
print("AGD FULL VALIDATION SUITE")
print("="*70)


tests=[
    ("LINEAR",linear_T),
    ("NONLINEAR",nonlinear_T)
]


for name,T in tests:


    print()
    print("SYSTEM:",name)


    for N in N_VALUES:


        print()
        print("N =",N)



        t=time.time()

        a,b=bfs(N,T)

        bt=time.time()-t



        t=time.time()

        c,d=quotient(N,T)

        qt=time.time()-t



        print("BFS:",
              a,
              "states",
              b,
              "time",
              round(bt,4))


        print("QUOTIENT:",
              c,
              "classes",
              d,
              "time",
              round(qt,4))


        print("TRANSPORT:",
              a==c)


        print("COMPRESSION:",
              round(b/max(d,1),2))


print()
print("VALIDATION COMPLETE")

