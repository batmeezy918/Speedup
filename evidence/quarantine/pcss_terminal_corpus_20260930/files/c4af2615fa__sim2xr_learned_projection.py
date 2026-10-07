#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd


print("="*70)
print("SIM2XR-C LEARNED PROJECTION DISCOVERY")
print("Optimize Pi for predictive equivalence")
print("="*70)



# ============================================================
# LOAD DATA
# ============================================================

files=[]

for root,dirs,fs in os.walk("."):

    for f in fs:

        if f.endswith(".csv"):
            files.append(
                os.path.join(root,f)
            )


if not files:

    print("No csv found")
    exit()


file=files[0]

print("\nUsing:")
print(file)



df=pd.read_csv(file)


X=df.select_dtypes(
    include=[np.number]
).values


X=X[np.all(np.isfinite(X),axis=1)]


mean=X.mean(axis=0)
std=X.std(axis=0)+1e-12


X=(X-mean)/std



X0=X[:-1]
X1=X[1:]


N,D=X0.shape


print("Dimension:",D)



# ============================================================
# LEARNED PROJECTION
# ============================================================


best=None



for K in range(1,D):


    print("\nSearching latent dimension:",K)



    # random projection initialization

    W=np.random.randn(K,D)

    W=W/np.linalg.norm(
        W,
        axis=1,
        keepdims=True
    )



    lr=0.001


    for epoch in range(2000):


        Q0=X0 @ W.T
        Q1=X1 @ W.T



        # latent linear dynamics

        A=np.linalg.lstsq(
            Q0,
            Q1,
            rcond=None
        )[0]



        P=Q0 @ A



        error=P-Q1



        # gradient for W

        grad=(

            error.T @ X0

            -

            A.T @ error.T @ X1

        ) / N



        W-=lr*grad



        # normalize

        W=W/(
            np.linalg.norm(
                W,
                axis=1,
                keepdims=True
            )+1e-12
        )



    # final model


    Q0=X0@W.T
    Q1=X1@W.T


    A=np.linalg.lstsq(
        Q0,
        Q1,
        rcond=None
    )[0]



    pred=Q0@A



    traj_error=np.mean(
        np.linalg.norm(
            pred-Q1,
            axis=1
        )
    )



    reconstruction=Q0@W


    roundtrip=np.max(
        np.linalg.norm(
            X0-reconstruction,
            axis=1
        )
    )



    eig=np.linalg.eigvals(A)

    contraction=max(
        np.abs(eig)
    )



    score=traj_error+0.1*roundtrip



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
            "W":W,
            "A":A,
            "traj":traj_error,
            "round":roundtrip,
            "lambda":contraction,
            "score":score

        }



# ============================================================
# FINAL CERTIFICATION
# ============================================================


print("\n"+"="*70)
print("FINAL SIM2XR-C LEARNED QUOTIENT")
print("="*70)


print(
"Original:",
D
)


print(
"Latent:",
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
"quotient_lambda:",
best["lambda"]
)



CERTIFIED=(

    best["lambda"] < 1

    and

    best["traj"] < 0.1

)



print()


if CERTIFIED:

    print("CERTIFIED : TRUE")

else:

    print("CERTIFIED : FALSE")


print("="*70)
