"""Forward quotient operator Q. Specimen must supply an artifact hash.

Returns None until a real quotient witness is attached. None is not a pass.
"""

def forward(state, witness_hash: str | None):
    if not witness_hash:
        return None
    return {"reduced": state, "quotient_hash": witness_hash}
