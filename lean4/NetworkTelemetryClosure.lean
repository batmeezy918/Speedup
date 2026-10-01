namespace NetworkTelemetryPCSS

structure Telemetry where
  target : String
  latency : Nat
  loss : Nat

def Q (x : Telemetry) : Telemetry := x

def R (x : Telemetry) : Telemetry := x

theorem reconstruction_closure (x : Telemetry) : R (Q x) = x := by
  rfl

theorem target_preserved (x : Telemetry) : (R (Q x)).target = x.target := by
  rfl

theorem latency_preserved (x : Telemetry) : (R (Q x)).latency = x.latency := by
  rfl

theorem loss_preserved (x : Telemetry) : (R (Q x)).loss = x.loss := by
  rfl

end NetworkTelemetryPCSS
