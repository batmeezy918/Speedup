import AGD_C_KERNEL_FLOAT_CORRESPONDENCE
open AGD.CFloat
def U0 : Nat → Nat → Float := fun b c =>
  match b, c with
  | 0, 0 => 0.1   | 0, 1 => 0.3   | 0, _ => -0.7
  | 1, 0 => 1.0/3.0 | 1, 1 => 2.5 | 1, _ => 0.2
  | 2, 0 => -0.9  | 2, 1 => 0.6   | 2, _ => 1.0/7.0
  | _, _ => 0.0
def x0 : CState := fun b _ => 0.1*(Float.ofNat (b+1))/(Float.ofNat (b+2))
def r0 : Nat := 3
def m0 : Nat := 4
-- C says X_BITS: 4587366580439587226 4589468260265693457 4590068740216009524
#eval (Float.toBits (x0 0 0)).toNat
#eval (Float.toBits (x0 1 0)).toNat
#eval (Float.toBits (x0 2 0)).toNat
-- C says FULL1: 13806955593607371818 4596313731699296611 4573238145037150638
def s1 := cOriginalApply U0 r0 m0 x0
#eval (Float.toBits (s1 0 0)).toNat
#eval (Float.toBits (s1 1 0)).toNat
#eval (Float.toBits (s1 2 0)).toNat
def s2 := cOriginalApply U0 r0 m0 s1
#eval (Float.toBits (s2 0 0)).toNat
#eval (Float.toBits (s2 1 0)).toNat
#eval (Float.toBits (s2 2 0)).toNat
def s3 := cOriginalApply U0 r0 m0 s2
#eval (Float.toBits (s3 0 0)).toNat
#eval (Float.toBits (s3 1 0)).toNat
#eval (Float.toBits (s3 2 0)).toNat
def q3 := cReconstruct m0 (iterateC (cQuotientApply U0 r0) 3 (cProject x0))
#eval (Float.toBits (q3 0 0)).toNat
#eval (Float.toBits (q3 1 0)).toNat
#eval (Float.toBits (q3 2 0)).toNat
