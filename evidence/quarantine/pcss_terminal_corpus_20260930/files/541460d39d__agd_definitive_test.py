import time
import random
from collections import deque


# ============================================================
# AGD DEFINITIVE GENERALIZATION TEST
# Nonlinear transition + quotient transport validation
# ============================================================


N = 5_000_000

START = 0
GOAL = N - 1

BUCKET = 5000

random.seed(42)


# ------------------------------------------------------------
# NONLINEAR TRANSITION OPERATOR T
# ------------------------------------------------------------

def neighbors(x):

    moves = [
        x + 1,
        x + 7,
        x * 2 + 1,
        x // 2
    ]

    for m in moves:

        if 0 <= m < N:
            yield m



# ------------------------------------------------------------
# BFS ORIGINAL
# ------------------------------------------------------------

def bfs(limit=2000000):

    q = deque([START])

    visited = {START}

    expanded = 0


    while q:

        x = q.popleft()

        expanded += 1


        if x == GOAL:

            return True, expanded


        if expanded >= limit:

            return False, expanded


        for y in neighbors(x):

            if y not in visited:

                visited.add(y)
                q.append(y)



    return False, expanded




# ------------------------------------------------------------
# QUOTIENT OPERATOR
# ------------------------------------------------------------


def Q(x):

    return x // BUCKET



# ------------------------------------------------------------
# QUOTIENT BFS
# ------------------------------------------------------------

def quotient_bfs():


    start = Q(START)
    goal = Q(GOAL)


    q = deque([start])

    visited = {start}

    expanded = 0



    while q:


        cls = q.popleft()

        expanded += 1


        if cls == goal:

            return True, expanded



        begin = cls * BUCKET

        end = min(
            begin + BUCKET,
            N
        )


        for x in range(begin,end):


            for y in neighbors(x):


                yc = Q(y)


                if yc not in visited:

                    visited.add(yc)

                    q.append(yc)



    return False, expanded




# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------


print("="*70)
print("AGD DEFINITIVE GENERALIZATION TEST")
print("="*70)

print("N =",N)



t=time.perf_counter()

bf,bn=bfs()

bt=time.perf_counter()-t



t=time.perf_counter()

qf,qn=quotient_bfs()

qt=time.perf_counter()-t



print()

print("BRUTE FORCE")
print("Found:",bf)
print("Expanded:",bn)
print("Time:",round(bt,6))


print()

print("QUOTIENT")
print("Found:",qf)
print("Expanded:",qn)
print("Time:",round(qt,6))


print()

compression = bn/max(qn,1)

print("Compression:",compression)

print("TRANSPORT:",bf==qf)


if bf==qf:

    print()
    print("AGD TRANSPORT INVARIANCE VERIFIED")

else:

    print()
    print("FAIL: REACHABILITY LOST")

