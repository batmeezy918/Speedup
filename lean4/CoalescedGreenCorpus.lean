/-!
# Coalesced GREEN Lean4 Corpus

Single import surface for the operationally relevant proved theorem modules
already present in this repository. This file establishes no new theorem
about external implementations; it only creates a stable import boundary.
-/

import SpeedupLean
import BidirectionalGapClosure

namespace CoalescedGreenCorpus

/-- Stable marker exposing the coalesced proof surface to downstream clients. -/
theorem coalesced_green_kernel_available : True := by
  trivial

end CoalescedGreenCorpus
