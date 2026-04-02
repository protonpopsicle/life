"""Elements, energy, universe state, greedy assembly, and finalization (chemistry milestone)."""

from __future__ import annotations

import json
import pprint
import sys
import time
from collections import Counter
from enum import Enum

# --- Energy (tunable) ---
INITIAL_ENERGY = 10_000
ENERGY_FORM_BOND = 1  # each bond in a finalized molecule debits this much on finalize
ENERGY_RELEASE_BREAK = 1  # gained when a bond breaks (future use)

# Total bonds per target molecule (used only at finalize; greedy assembly unchanged)
FINALIZE_BOND_COST = {
    "O2": 1,
    "CO2": 2,
    "H2O": 2,
}

# the most common elements in living organisms
# all bytes read into the program will be mapped to these elements
Elem = Enum("Elem", ["C", "H", "O", "N", "P", "S"])

# Canonical target compositions: element *sequence* only. Actual state always stores raw bytes;
# element identity is always from get_type(byte) — never Enum values embedded in buffers.
MOLECULE_TARGETS = {
    "O2": (Elem.O, Elem.O),
    "CO2": (Elem.C, Elem.O, Elem.O),
    "H2O": (Elem.H, Elem.H, Elem.O),
}


class Universe:
    """Single place for simulation state: energy, free vs in-partial atoms, completed molecules."""

    def __init__(self, energy=None):
        self.energy = INITIAL_ENERGY if energy is None else energy
        self.free_atoms = bytearray()
        self.molecules = []
        self.o2_partials = []
        self.co2_partials = []
        self.h2o_partials = []

    def total_atoms_accounted(self):
        """Every input byte should appear exactly once across these buckets."""
        n = len(self.free_atoms)
        for partials in (self.o2_partials, self.co2_partials, self.h2o_partials):
            n += sum(len(p) for p in partials)
        for m in self.molecules:
            n += len(m[1]) if isinstance(m, tuple) else len(m)
        return n


def get_info(bytes_collection):
    return "".join([Elem(x % len(Elem) + 1).name for x in bytes_collection])


def get_type(byte):
    _index = int.from_bytes(byte, byteorder=sys.byteorder) % len(Elem) + 1
    return Elem(_index)


def _partial_molecule_kind(partial):
    """If partial matches a MOLECULE_TARGETS pattern (by element sequence on raw bytes), return its kind."""
    for kind, elems in MOLECULE_TARGETS.items():
        if len(partial) != len(elems):
            continue
        if all(get_type(partial[i : i + 1]) == elems[i] for i in range(len(elems))):
            return kind
    return None


def finalize_complete_partials(universe):
    """Move complete partials into universe.molecules; debit energy by bond count. If energy is insufficient, leave the partial open (no finalization)."""

    def sweep(partials):
        kept = []
        for p in partials:
            kind = _partial_molecule_kind(p)
            if kind is None:
                kept.append(p)
                continue
            cost = FINALIZE_BOND_COST[kind] * ENERGY_FORM_BOND
            if universe.energy < cost:
                kept.append(p)
                continue
            universe.energy -= cost
            universe.molecules.append((kind, bytes(p)))
        return kept

    universe.o2_partials = sweep(universe.o2_partials)
    universe.co2_partials = sweep(universe.co2_partials)
    universe.h2o_partials = sweep(universe.h2o_partials)


def _free_atoms_by_elem(free_atoms):
    c = Counter()
    for b in free_atoms:
        c[get_type(bytes([b])).name] += 1
    return dict(c)


def observation_snapshot(universe, bytes_read, *, phase, atoms_accounted=None):
    """Structured row for JSON logging (one line per call when piping logs)."""
    completed = Counter(k for k, _ in universe.molecules)
    row = {
        "t": time.time(),
        "phase": phase,
        "bytes_read": bytes_read,
        "energy": universe.energy,
        "free_atoms": len(universe.free_atoms),
        "free_atoms_by_elem": _free_atoms_by_elem(universe.free_atoms),
        "partials": {
            "o2": len(universe.o2_partials),
            "co2": len(universe.co2_partials),
            "h2o": len(universe.h2o_partials),
        },
        "molecules_completed": len(universe.molecules),
        "completed_by_kind": dict(completed),
    }
    if atoms_accounted is not None:
        row["atoms_accounted"] = atoms_accounted
    return row


def big_bang(
    path="input.pdf",
    *,
    initial_energy=None,
    log_every_n_bytes=0,
    verbose=False,
    emit_line=None,
):
    """
    Read bytes from path, route into partials / free pool, finalize, verify accounting.

    emit_line: if set, called with one dict per JSON log line (batch and final).
    """
    universe = Universe(energy=initial_energy)
    bytes_read = 0

    with open(path, "rb") as f:
        byte = f.read(1)
        while byte != b"":
            bytes_read += 1
            _type = get_type(byte)
            if _type == Elem.C:
                universe.co2_partials.append(bytearray(byte))
            elif _type == Elem.H:
                found = False
                for partial in universe.h2o_partials:
                    if len(partial) == 1:
                        partial += byte
                        found = True
                        break

                if not found:
                    universe.h2o_partials.append(bytearray(byte))
            elif _type == Elem.O:
                found = False
                for partial in universe.h2o_partials:
                    if len(partial) == 2:
                        partial += byte
                        found = True
                        break

                if found:
                    byte = f.read(1)
                    continue

                for partial in universe.co2_partials:
                    if len(partial) < 3:
                        partial += byte
                        found = True
                        break

                if found:
                    byte = f.read(1)
                    continue

                for partial in universe.o2_partials:
                    if len(partial) == 1:
                        partial += byte
                        found = True
                        break

                if not found:
                    universe.o2_partials.append(bytearray(byte))
            else:
                # N, P, S — no bonding rules yet; keep in the free pool
                universe.free_atoms.extend(byte)

            if (
                emit_line
                and log_every_n_bytes
                and bytes_read % log_every_n_bytes == 0
            ):
                emit_line(observation_snapshot(universe, bytes_read, phase="batch"))

            byte = f.read(1)

    finalize_complete_partials(universe)

    accounted = universe.total_atoms_accounted()
    if accounted != bytes_read:
        raise RuntimeError(
            f"byte accounting mismatch: read {bytes_read}, accounted {accounted}"
        )

    if emit_line:
        emit_line(
            observation_snapshot(
                universe, bytes_read, phase="final", atoms_accounted=accounted
            )
        )

    if verbose:
        completed_kinds = Counter(k for k, _ in universe.molecules)
        pprint.pp(
            {
                "energy": universe.energy,
                "free_atoms": len(universe.free_atoms),
                "molecules_completed": len(universe.molecules),
                "completed_by_kind": dict(completed_kinds),
                "bytes_read": bytes_read,
                "atoms_accounted": accounted,
            }
        )
        pprint.pp({"completed_molecules_sample": universe.molecules[:8]})
        # pprint.pp({"O2": [get_info(partial) for partial in universe.o2_partials]})
        # pprint.pp({"CO2": [get_info(partial) for partial in universe.co2_partials]})
        # pprint.pp({"H2O": [get_info(partial) for partial in universe.h2o_partials]})
    return universe
