"""Diagnostics helpers for LinkPower Battery."""

from __future__ import annotations


def packet_diff(previous: str | None, current: str | None) -> str | None:
    """Return byte-by-byte packet differences."""
    if not previous or not current:
        return None

    old = previous.split("-")
    new = current.split("-")

    changes = []

    for index, (old_byte, new_byte) in enumerate(zip(old, new)):
        if old_byte != new_byte:
            changes.append(f"byte_{index}: {old_byte} → {new_byte}")

    if not changes:
        return "No changes"

    return "\n".join(changes)
