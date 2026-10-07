#!/usr/bin/env python3

import os
import numpy as np
import pandas as pd

print("="*70)
print("SIM2XR-C REAL DATA DISCOVERY RUNNER")
print("trajectory -> quotient -> dynamics -> verification")
print("="*70)


# ============================================================
# 1. FIND DATASET
# ============================================================

def find_files():

    results=[]

    for root,dirs,files in os.walk("."):

        for f in files:

            if f.endswith(".csv") or f.endswith(".h5") or f.endswith(".hdf5"):
                results.append(
                    os.path.join(root,f)
                )

    return results



files=find_files()


if len(files)==0:

    print("NO DATA FILE FOUND")
    print("Place csv/hdf5 trajectory file in this directory")

    exit()


print("\nFOUND FILES:")

for i,f in enumerate(files[:10]):

    print(i,f)


file=files[0]


print("\nUSING:")
print(file)



# ============================================================
# 2. LOAD DATA
# ============================================================


if file.endswith(".csv"):

    df=pd.read_csv(file)

    data=df.select_dtypes(
        include=[np.number]
    ).values


else:

    import h5py

    with h5py.File(file,"r") as h:

        keys=list(h.keys())

        print("HDF KEYS:",keys)

        arr=h[keys[0]][:]

        data=np.array(arr)



data=np.asarray(data)


print("\nRAW SHAPE:")
print(data.shape)



# ============================================================
# 3. CLEAN DATA
# ============================================================


data=data[np.all(np.isfinite(data),axis=1)]


mean=data.mean(axis=0)

std=data.std(axis=0)+1e-12


X=(data-mean)/std



D=X.shape[1]


print("\nDIMENSION:")
print(D)



# ============================================================
# 4. CREATE TRAIN / TEST
# ============================================================


states=X[:-1]

future=X[1:]



# ============================================================
# 5. DISCOVER QUOTIENT
# ============================================================


U,S,Vt=np.linalg.svd(
    states,
    full_matrices=False
)


# choose compressed dimension

K=max(
    1,
    min(
        D//2,
        4
    )
)


Pi=Vt[:K]


def project(x):

    return Pi @ x



def lift(q):

    return Pi.T @ q



QX=np.array(
    [
        project(x)
        for x in states
    ]
)


QY=np.array(
    [
        project(x)
        for x in future
    ]
)



print("\nQUOTIENT DIMENSION:")
print(K)

print("COMPRESSION:")
print(D/K)



# ============================================================
# 6. LEARN QUOTIENT DYNAMICS
# ============================================================


A=np.hstack(
    [
        QX,
        np.ones((len(QX),1))
    ]
)


params=np.linalg.lstsq(
    A,
    QY,
    rcond=None
)[0]


M=params[:-1]

b=params[-1]



def Fq(q):

    return M.T @ q + b



# ============================================================
# 7. BOUND ERROR
# ============================================================


traj=[]


q=QX[0]


for i in range(min(200,len(QX))):

    q=Fq(q)

    traj.append(q)



traj=np.array(traj)


truth=QY[:len(traj)]



trajectory_error=np.mean(
    np.linalg.norm(
        traj-truth,
        axis=1
    )
)


trajectory_max=np.max(
    np.linalg.norm(
        traj-truth,
        axis=1
    )
)



# ============================================================
# 8. ROUNDTRIP
# ============================================================


recon=[]


for x in states:

    q=project(x)

    xr=lift(q)

    recon.append(
        np.linalg.norm(
            x-xr
        )
    )


roundtrip=max(recon)



# ============================================================
# 9. CONTRACTION ESTIMATE
# ============================================================


eig=np.linalg.eigvals(M)

lambda_q=max(
    np.abs(eig)
)



# ============================================================
# OUTPUT
# ============================================================


print("\n"+"="*70)
print("SIM2XR-C REPORT")
print("="*70)


print(
"projection_roundtrip_error =",
roundtrip
)


print(
"trajectory_mean_error =",
trajectory_error
)


print(
"trajectory_max_error =",
trajectory_max
)


print(
"quotient_contraction_estimate =",
lambda_q
)



CERTIFIED=(

    lambda_q < 1
    and
    trajectory_error < 0.1

)



print()

if CERTIFIED:

    print("CERTIFIED : TRUE")

else:

    print("CERTIFIED : FALSE")


print("="*70)
