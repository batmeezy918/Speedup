import time
from collections import deque


# ============================================================
# AGD INVARIANT QUOTIENT TEST
# Dynamic equivalence validation
# ============================================================


N = 5_000_000

START = 0
GOAL = N - 1

BUCKET = 5000


# ------------------------------------------------------------
# TRANSITION OPERATOR T
# ------------------------------------------------------------

def neighbors(x):

    moves = [
        x + 1,
        x + 7,
        x * 2 + 1,
        x // 2
    ]

    for y in moves:

        if 0 <= y < N:
            yield y



# ------------------------------------------------------------
# ORIGINAL BFS
# ------------------------------------------------------------

def bfs(limit=2000000):

    q = deque([START])

    visited = {START}

    expanded = 0


    while q:

        x=q.popleft()

        expanded+=1


        if x==GOAL:
            return True,expanded


        if expanded>=limit:
            return False,expanded


        for y in neighbors(x):

            if y not in visited:

                visited.add(y)
                q.append(y)



    return False,expanded




# ------------------------------------------------------------
# QUOTIENT OPERATOR
# ------------------------------------------------------------

def Q(x):

    return x//BUCKET




# ------------------------------------------------------------
# TRANSITION SIGNATURE
# ------------------------------------------------------------

def signature(x):

    return tuple(
        sorted(
            Q(y)
            for y in neighbors(x)
        )
    )



# ------------------------------------------------------------
# VALIDATED QUOTIENT MAP
# ------------------------------------------------------------

def valid_class(cls):

    begin = cls*BUCKET

    end=min(
        begin+BUCKET,
        N
    )


    sig=None


    for x in range(begin,end):

        s=signature(x)


        if sig is None:

            sig=s


        elif s!=sig:

            return False


    return True




# ------------------------------------------------------------
# VALIDATED QUOTIENT BFS
# ------------------------------------------------------------

def quotient_bfs():


    start=Q(START)

    goal=Q(GOAL)


    q=deque([start])

    visited={start}


    expanded=0


    while q:


        cls=q.popleft()

        expanded+=1


        if cls==goal:

            return True,expanded



        if not valid_class(cls):

            continue



        begin=cls*BUCKET

        end=min(
            begin+BUCKET,
            N
        )


        for x in range(begin,end):


            for y in neighbors(x):


                yc=Q(y)


                if yc not in visited:

                    visited.add(yc)

                    q.append(yc)



    return False,expanded





# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------


print("="*70)
print("AGD INVARIANT QUOTIENT TEST")
print("="*70)

print("N =",N)



t=time.perf_counter()

bf,be=bfs()

bt=time.perf_counter()-t



t=time.perf_counter()

qf,qe=quotient_bfs()

qt=time.perf_counter()-t



print()

print("BFS")
print("Found:",bf)
print("Expanded:",be)
print("Time:",round(bt,6))


print()

print("VALIDATED QUOTIENT")
print("Found:",qf)
print("Expanded:",qe)
print("Time:",round(qt,6))


print()

print("Compression:",
      round(be/max(qe,1),2))


print("TRANSPORT:",
      bf==qf)


if bf==qf:

    print()
    print("TRANSPORT INVARIANCE VERIFIED")

else:

    print()
    print("REJECTED: INVALID QUOTIENT")

