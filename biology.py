"""Biology layer: depends on chemistry only (no circular imports)."""

from __future__ import annotations

import time
from collections import Counter
from typing import Iterable, MutableSequence

from chemistry import (
    ENERGY_FORM_BOND,
    ENERGY_RELEASE_BREAK,
    Elem,
    FINALIZE_BOND_COST,
    Universe,
    get_type,
)

# Metabolism v1: all energy debits come from ``Universe.energy`` (shared pool with chemistry).
UPTAKE_ENERGY_PER_ATOM = 1


class Cell:
    def __init__(self, name="bob", age=0, *, max_age_ticks: int | None = None):
        self.name = name
        self.ticks = age
        self.max_age_ticks = max_age_ticks
        self.alive = True
        self.size = 0
        self.storage = bytearray()

    def __str__(self):
        return f"{self.name}({self.ticks})"

    def photosynthesis(self, light, water, carbon_dioxide):
        """Deferred to a later milestone (see BIOLOGY_CELL_MILESTONE_PLAN.md)."""
        raise NotImplementedError("photosynthesis is not implemented in this milestone")

    def ingest(self, nutribytes: MutableSequence, targets: Iterable[Elem]) -> None:
        """Move atoms whose element type is in *targets* from *nutribytes* into ``self.storage``.

        *nutribytes* is **mutated in place**; matching units are removed. Supported:

        - ``bytearray``: each byte is one atom; uses ``get_type(byte[i:i+1])``.
        - ``list`` of length-1 ``bytes`` objects (e.g. ``[b'x', b'y']``).

        *targets* is any iterable of ``Elem``; coerced to a set for membership.

        No energy is debited here (direct ``ingest`` is a manual buffer move). Paid uptake
        from the world uses ``ChemEnvironment.uptake_free_atoms`` instead.

        Invariant: no new byte values are invented; existing values are only relocated.
        """
        tset = set(targets)
        if isinstance(nutribytes, bytearray):
            remain = bytearray()
            for i in range(len(nutribytes)):
                chunk = nutribytes[i : i + 1]
                if get_type(chunk) in tset:
                    self.storage.extend(chunk)
                else:
                    remain.append(nutribytes[i])
            nutribytes[:] = remain
            return
        if isinstance(nutribytes, list):
            kept: list[bytes] = []
            for nb in nutribytes:
                if len(nb) != 1:
                    raise ValueError("each list entry must be length-1 bytes")
                if get_type(nb) in tset:
                    self.storage.extend(nb)
                else:
                    kept.append(nb)
            nutribytes[:] = kept
            return
        raise TypeError(
            "nutribytes must be bytearray or list of length-1 bytes objects"
        )


def closed_atom_count(universe: Universe, cell: Cell) -> int:
    """Atoms in the universe buckets plus bytes still inside ``cell.storage`` (closed world)."""
    return universe.total_atoms_accounted() + len(cell.storage)


def cell_observation_row(
    universe: Universe,
    cell: Cell,
    *,
    tick_index: int,
    metabolism: dict,
) -> dict:
    """One JSON-serializable row per cell metabolism tick (``phase``: ``cell_tick``)."""
    by_elem = Counter()
    for b in cell.storage:
        by_elem[get_type(bytes([b])).name] += 1
    return {
        "t": time.time(),
        "phase": "cell_tick",
        "tick_index": tick_index,
        "cell": {
            "name": cell.name,
            "ticks": cell.ticks,
            "alive": cell.alive,
            "max_age_ticks": cell.max_age_ticks,
            "storage_len": len(cell.storage),
            "storage_by_elem": dict(by_elem),
        },
        "universe_energy": universe.energy,
        "closed_atom_count": closed_atom_count(universe, cell),
        "metabolism": metabolism,
    }


def cell_final_observation_row(universe: Universe, cell: Cell, *, ticks_run: int) -> dict:
    """Summary line after the cell loop (``phase``: ``cell_complete``)."""
    by_elem = Counter()
    for b in cell.storage:
        by_elem[get_type(bytes([b])).name] += 1
    return {
        "t": time.time(),
        "phase": "cell_complete",
        "ticks_run": ticks_run,
        "cell": {
            "name": cell.name,
            "ticks": cell.ticks,
            "alive": cell.alive,
            "max_age_ticks": cell.max_age_ticks,
            "storage_len": len(cell.storage),
            "storage_by_elem": dict(by_elem),
        },
        "universe_energy": universe.energy,
        "closed_atom_count": closed_atom_count(universe, cell),
    }


def closed_world_self_test() -> None:
    """Assert atom conservation through uptake, metabolism, and age death (fixed bytes)."""
    u = Universe(energy=10_000)
    u.free_atoms.extend(b"\x2a\x2b\x5c")
    n = u.total_atoms_accounted()
    c = Cell(max_age_ticks=4)
    env = ChemEnvironment(u)
    assert closed_atom_count(u, c) == n
    env.uptake_free_atoms(c, list(Elem), max_count=2)
    assert closed_atom_count(u, c) == n
    for _ in range(8):
        env.metabolism_tick(c, list(Elem), max_uptake=4)
    assert closed_atom_count(u, c) == n


class ChemEnvironment:
    """Minimal view of chemistry state for the cell.

    The cell never creates bytes; it only moves atoms between shared buffers and
    ``Cell.storage``. **v1 feeding source:** ``Universe.free_atoms`` only (completed
    molecules and partials are not consumed here yet).

    **Energy (v1):** metabolic costs debit ``Universe.energy`` only (no separate cell
    pool). Closed-world atom counts are ``universe`` buckets plus ``cell.storage`` —
    ``Universe.total_atoms_accounted()`` does not include the cell; use
    ``closed_atom_count(universe, cell)`` for conservation checks.

    **Death (v1):** if ``Cell.max_age_ticks`` is set, ``metabolism_tick`` ends the cell
    when ``ticks`` reaches that limit, returning storage to ``free_atoms`` and crediting
    ``ENERGY_RELEASE_BREAK`` per byte.
    """

    __slots__ = ("universe",)

    def __init__(self, universe: Universe):
        self.universe = universe

    def uptake_free_atoms(
        self,
        cell: Cell,
        targets: Iterable[Elem],
        *,
        max_count: int | None = None,
        energy_per_atom: int = UPTAKE_ENERGY_PER_ATOM,
    ) -> int:
        """Move matching atoms from ``universe.free_atoms`` into ``cell.storage``.

        Each moved atom debits ``energy_per_atom`` from ``universe.energy``. If the
        pool is insufficient for the next atom, that byte stays in ``free_atoms``.

        Scans left to right; stops after ``max_count`` successful moves when set.

        Returns the number of bytes moved.
        """
        tset = set(targets)
        fa = self.universe.free_atoms
        remain = bytearray()
        moved = 0
        u = self.universe
        for i in range(len(fa)):
            chunk = fa[i : i + 1]
            can_move = (
                (max_count is None or moved < max_count)
                and get_type(chunk) in tset
                and u.energy >= energy_per_atom
            )
            if can_move:
                u.energy -= energy_per_atom
                cell.storage.extend(chunk)
                moved += 1
            else:
                remain.append(fa[i])
        fa[:] = remain
        return moved

    def release_completed_molecule_to_free_atoms(self, kind: str | None = None) -> bool:
        """Remove one completed molecule from ``universe.molecules``; append its bytes to ``free_atoms``.

        Debits ``FINALIZE_BOND_COST[kind] * ENERGY_FORM_BOND`` from ``universe.energy``
        (same scale as forming the molecule). If energy is insufficient, state is unchanged.

        ``kind`` selects the first ``(kind, payload)`` with that label; if ``None``, the
        first molecule in the list is used. Returns whether a molecule was released.
        """
        mols = self.universe.molecules
        idx: int | None
        if not mols:
            return False
        if kind is None:
            idx = 0
        else:
            idx = next((i for i, (k, _) in enumerate(mols) if k == kind), None)
            if idx is None:
                return False
        k, payload = mols[idx]
        cost = FINALIZE_BOND_COST[k] * ENERGY_FORM_BOND
        if self.universe.energy < cost:
            return False
        self.universe.energy -= cost
        mols.pop(idx)
        self.universe.free_atoms.extend(payload)
        return True

    def decompose_cell_to_free_atoms(self, cell: Cell) -> int:
        """Return every byte in ``cell.storage`` to ``universe.free_atoms`` and clear storage.

        Credits ``ENERGY_RELEASE_BREAK`` per byte to ``universe.energy`` (notional bond
        break). Does not change ``cell.alive``; pair with ``kill_and_decompose`` or the
        age-death path in ``metabolism_tick`` as needed.

        Returns the number of bytes returned.
        """
        payload = bytes(cell.storage)
        n = len(payload)
        if n == 0:
            return 0
        self.universe.free_atoms.extend(payload)
        cell.storage.clear()
        self.universe.energy += n * ENERGY_RELEASE_BREAK
        return n

    def kill_and_decompose(self, cell: Cell) -> int:
        """Decompose ``cell.storage`` into ``free_atoms`` and set ``cell.alive`` False."""
        n = self.decompose_cell_to_free_atoms(cell)
        cell.alive = False
        return n

    def metabolism_tick(
        self,
        cell: Cell,
        uptake_targets: Iterable[Elem],
        *,
        max_uptake: int = 8,
        energy_per_atom: int = UPTAKE_ENERGY_PER_ATOM,
    ) -> dict:
        """One simple metabolic step: paid uptake from ``free_atoms`` only (v1).

        Increments ``cell.ticks`` first. If ``cell.max_age_ticks`` is set and ticks reach
        that limit, the cell **dies**: storage is decomposed into ``free_atoms``, energy
        is credited per byte, ``cell.alive`` becomes False, and uptake is skipped.

        Returns a small summary dict for logging.
        """
        if not cell.alive:
            return {
                "alive": False,
                "died": False,
                "uptake_moved": 0,
                "returned_atoms": 0,
                "universe_energy": self.universe.energy,
            }

        cell.ticks += 1
        if cell.max_age_ticks is not None and cell.ticks >= cell.max_age_ticks:
            returned = self.decompose_cell_to_free_atoms(cell)
            cell.alive = False
            return {
                "alive": False,
                "died": True,
                "uptake_moved": 0,
                "returned_atoms": returned,
                "universe_energy": self.universe.energy,
            }

        n = self.uptake_free_atoms(
            cell,
            uptake_targets,
            max_count=max_uptake,
            energy_per_atom=energy_per_atom,
        )
        return {
            "alive": True,
            "died": False,
            "uptake_moved": n,
            "returned_atoms": 0,
            "universe_energy": self.universe.energy,
        }


if __name__ == "__main__":
    u = Universe(energy=50)
    u.free_atoms.extend(b"\x00\x01\x02")
    env = ChemEnvironment(u)
    c = Cell(max_age_ticks=2)
    before = closed_atom_count(u, c)
    moved = env.uptake_free_atoms(c, [Elem.C, Elem.H, Elem.O], max_count=2)
    t1 = env.metabolism_tick(c, [Elem.C, Elem.H, Elem.O], max_uptake=8)
    t2 = env.metabolism_tick(c, [Elem.C, Elem.H, Elem.O], max_uptake=8)
    after = closed_atom_count(u, c)
    print(
        {
            "biology_demo": True,
            "cell": str(c),
            "cell_alive": c.alive,
            "closed_atoms_before": before,
            "closed_atoms_after": after,
            "uptake_moved_first_call": moved,
            "metabolism_tick_1": t1,
            "metabolism_tick_2": t2,
            "universe_energy": u.energy,
            "free_atoms_left": len(u.free_atoms),
            "storage_len": len(c.storage),
        }
    )
