"""Reverse reconstruction operator Qinv. Missing witness is not a pass."""

def reverse(reduced, witness_hash: str | None):
    if not witness_hash:
        return None
    return {"reconstructed": reduced, "reverse_hash": witness_hash}
