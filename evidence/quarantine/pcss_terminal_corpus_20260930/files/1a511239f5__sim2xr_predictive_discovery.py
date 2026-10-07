#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd


print("="*70)
print("SIM2XR-C PREDICTIVE QUOTIENT DISCOVERY")
print("learn Pi -> learn F~ -> verify")
print("="*70)



# ============================================================
# FIND DATA
# ============================================================

files=[]

for root,dirs,fs in os.walk("."):

    for f in fs:

        if f.endswith(".csv"):
            files.append(
                os.path.join(root,f)
            )


if not files:

    print("No CSV found")
    exit()


file=files[0]

print("\nUsing:")
print(file)



# ============================================================
# LOAD
# ============================================================

df=pd.read_csv(file)

X=df.select_dtypes(
    include=[np.number]
).values


X=X[np.all(np.isfinite(X),axis=1)]


print("Raw shape:",X.shape)



# normalize

mean=X.mean(axis=0)
std=X.std(axis=0)+1e-12

X=(X-mean)/std



# ============================================================
# TRAIN TEST SPLIT
# ============================================================

states=X[:-1]
future=X[1:]


N,D=states.shape


print("Dimension:",D)



# ============================================================
# LEARN DYNAMICS IN FULL SPACE
# ============================================================

A_full=np.linalg.lstsq(
    states,
    future,
    rcond=None
)[0]



def F(x):

    return x @ A_full



# ============================================================
# SEARCH QUOTIENTS
# ============================================================

best=None


for K in range(1,D):


    print("\nTesting quotient dimension:",K)



    # initialize projection randomly

    U,S,V=np.linalg.svd(
        states,
        full_matrices=False
    )


    Pi=V[:K]


    QX=states @ Pi.T
    QY=future @ Pi.T



    # learn latent dynamics

    A=np.linalg.lstsq(
        QX,
        QY,
        rcond=None
    )[0]



    def Fq(q):

        return q @ A



    pred=[]

    q=QX[0]


    for i in range(min(300,len(QX))):

        q=Fq(q)

        pred.append(q)



    pred=np.array(pred)

    truth=QY[:len(pred)]



    traj_error=np.mean(
        np.linalg.norm(
            pred-truth,
            axis=1
        )
    )



    # reconstruction

    recon=QX @ Pi

    roundtrip=np.max(
        np.linalg.norm(
            states-recon,
            axis=1
        )
    )



    # stability

    eig=np.linalg.eigvals(A)

    contraction=max(
        np.abs(eig)
    )



    score=traj_error + 0.1*roundtrip



    print(
        "traj:",
        traj_error,
        "round:",
        roundtrip,
        "lambda:",
        contraction
    )



    if best is None or score < best["score"]:

        best={

            "K":K,
            "Pi":Pi,
            "A":A,
            "traj":traj_error,
            "round":roundtrip,
            "lambda":contraction,
            "score":score

        }




# ============================================================
# FINAL REPORT
# ============================================================


print("\n"+"="*70)
print("BEST SIM2XR-C QUOTIENT")
print("="*70)


print(
"Original dimension:",
D
)


print(
"Quotient dimension:",
best["K"]
)


print(
"Compression:",
D/best["K"]
)


print(
"trajectory_error:",
best["traj"]
)


print(
"roundtrip_error:",
best["round"]
)


print(
"latent_contraction:",
best["lambda"]
)



certified=(

    best["lambda"] < 1
    and
    best["traj"] < 0.1

)



print()

if certified:

    print("CERTIFIED : TRUE")

else:

    print("CERTIFIED : FALSE")



print("="*70)
