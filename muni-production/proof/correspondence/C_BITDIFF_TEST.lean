import AGD_C_KERNEL_FLOAT_CORRESPONDENCE
open AGD.CFloat

/-- Inputs transcribed VERBATIM from c_bits.txt (the C binary's own stdout).
    Rational literals reproduce the exact doubles the C program computed. -/
def U0 : Nat → Nat → Float := fun b c =>
  match b, c with
  | 0, 0 => 0.1   | 0, 1 => 0.3   | 0, _ => -0.7
  | 1, 0 => 1.0/3.0 | 1, 1 => 2.5 | 1, _ => 0.2
  | 2, 0 => -0.9  | 2, 1 => 0.6   | 2, _ => 1.0/7.0
  | _, _ => 0.0

def x0 : CState := fun b _ => 0.1*(Float.ofNat (b+1))/(Float.ofNat (b+2))

def r0 : Nat := 3
def m0 : Nat := 4
def steps : Nat := 3

/-- The test vector is block-constant, as the gate requires. -/
example : CInvariant x0 := by intro b j k; rfl

/-- C: FULL1 bits 13806955593607371818 / 4596313731699296611 / 4573238145037150638 -/
example : (Float.toBits (cOriginalApply U0 r0 m0 x0 0 0)).toNat = 13806955593607371818 := by native_decide
example : (Float.toBits (cOriginalApply U0 r0 m0 x0 1 0)).toNat = 4596313731699296611 := by native_decide
example : (Float.toBits (cOriginalApply U0 r0 m0 x0 2 0)).toNat = 4573238145037150638 := by native_decide

/-- C: FULL3 bits 4587427314697419198 / 4608380468211094437 / 4598460982789154126 -/
example : (Float.toBits ((iterateC (cOriginalApply U0 r0 m0) steps x0) 0 0)).toNat = 4587427314697419198 := by native_decide
example : (Float.toBits ((iterateC (cOriginalApply U0 r0 m0) steps x0) 1 0)).toNat = 4608380468211094437 := by native_decide
example : (Float.toBits ((iterateC (cOriginalApply U0 r0 m0) steps x0) 2 0)).toNat = 4598460982789154126 := by native_decide

/-- C: QUOT bits -- the quotient path must land on the same doubles. -/
example : (Float.toBits (cReconstruct m0 (iterateC (cQuotientApply U0 r0) steps (cProject x0)) 0 0)).toNat = 4587427314697419198 := by native_decide
example : (Float.toBits (cReconstruct m0 (iterateC (cQuotientApply U0 r0) steps (cProject x0)) 1 0)).toNat = 4608380468211094437 := by native_decide
example : (Float.toBits (cReconstruct m0 (iterateC (cQuotientApply U0 r0) steps (cProject x0)) 2 0)).toNat = 4598460982789154126 := by native_decide
