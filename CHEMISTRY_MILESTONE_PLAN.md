# Plan: Next iteration of the Python sketch (chemistry milestone)

## Where things stand

The sketch already has a **byte stream → element label → greedy partial structures** pipeline, but it is **not yet “chemistry” in the intent sense**: there is **no energy**, **N/P/S are discarded**, **completed vs incomplete “molecules” are not distinguished**, and **`Cell` / metabolism is broken or out of scope** for a first milestone. Your intent file is explicit: **“Just getting the chemistry to work is a complete milestone.”**

So the **next iteration** should be a **chemistry-only milestone** that is **simple, rule-based, and observable**, without 2D space, plants, or DNA yet.

---

## Milestone: minimal working chemistry layer

### 1. Define a small simulation state (one place for rules)

Introduce a single object or module-level structure (keep it flat at first) that holds:

- **Energy** — a numeric pool; **bond formation subtracts**, **breaking releases** (constants you can tune). If energy is insufficient to complete a bond, **do not** form it (matches “no central planning” and “nothing from thin air”).
- **Atoms** — bytes or fixed records you never “destroy”; only **move** between *free* and *bonded* (even if implementation still uses buffers internally, the **invariant** is: every input byte is accounted for).
- **Molecules** — completed structures (and optionally open partials) with a **clear type** (O₂, CO₂, H₂O, or “unknown / polymer chunk” later).

This replaces the current pattern where `molecules = []` inside `big_bang` is a dead local and partials are only printed, not integrated into a persistent world state.

### 2. Finish the element routing (no dropped bytes)

Extend the assembler so **N, P, S** (and any future element) go into a **free-atom pool** instead of being ignored. That aligns with “decomposition returns to elemental state” later and fixes an obvious gap the analysis called out.

### 3. Separate “partial” from “complete” with energy on completion

Keep the existing greedy partial logic if you want, but add an explicit step:

- When a partial **reaches** the target composition for O₂ / CO₂ / H₂O, **check energy** for the **final bond** (or for the whole assembly, depending on how simple you want v1).
- If allowed: **finalize** — move from partial list to `molecules`, apply energy cost, store **immutable-ish** representation (e.g. `bytes` or a small `tuple` of bytes) for completed molecules.
- If not allowed: either **leave partial open** or **refuse the last bond** (pick one rule and document it in code comments only if needed).

That is the first real bridge between the docstring’s “bonds cost energy” and runnable code.

### 4. Make recipes and types consistent

The commented `molecular_recipe` mixes **Enum members inside `bytearray`**, which does not match how `big_bang` stores **raw bytes**. Next step: **one canonical representation** — e.g. always store **raw bytes** and derive element type with `get_type`, or store **element tags** only and drop raw bytes from molecules (tradeoff: loses “which byte” identity). For “data as atoms,” **keeping the original byte** in each slot is usually the right primitive.

*In code: `MOLECULE_TARGETS` gives target **element sequences**; partials and completed molecules keep **raw bytes**, with identity via `get_type`.*

### 5. Observability (lightweight “harness”)

Intent asks for something you can **watch while it runs**. Before pygame or a browser:

- **Structured logging**: after each batch (e.g. every N bytes or each finalized molecule), print or append one line of JSON or a fixed table: time, energy, counts of atoms/molecules by type.
- **CLI**: `input` path, initial energy, and verbosity so you can replay the same file.

That satisfies “debuggable while running” without building the 2D garden yet.

### 6. Code organization (only as much as the milestone needs)

When the chemistry logic is more than one screen, split **`chemistry.py`** (elements, bonding rules, energy, universe state) and keep **`smallthings.py`** as a thin `main` or rename it to `run_sim.py`. **Defer `Cell`, `photosynthesis`, and `ingest`** until chemistry can **produce** a stable stream of completed molecules and free atoms to feed a cell—fixing `ingest`’s `pop`-while-iterating bug belongs in that **biology** milestone, not this one.

---

## Order of work (suggested)

1. [x] **Universe state + energy constants + accounting for every byte**
2. [x] **Finalize molecules + energy checks** (O₂ / CO₂ / H₂O first)
3. [x] **N/P/S → free pool**
4. [x] **CLI + structured observation**
5. [x] **Extract `chemistry` module** — `chemistry.py` holds elements, energy, `Universe`, assembly, finalization, and `big_bang`; `smallthings.py` is the thin CLI plus deferred `Cell` stubs.
6. [x] **Stop here** — no 2D layout, wall-clock coupling, or visual plants in this milestone (revisit only after chemistry feels solid).

---

## Success criteria for this milestone

You can point to a run where:

- Energy **goes down** when bonds complete and **cannot** go negative for disallowed reactions.
- **No input bytes are silently dropped.**
- Completed O₂ / CO₂ / H₂O appear as **first-class objects** in state, not only as pretty-printed partials.
- You can **change one constant** (initial energy or bond cost) and **see** a different outcome in the log.

That is a defensible “next step” from the sketch toward the larger **Date Lifeforms** intent without jumping to multi-cellular visuals or fixing all biology stubs prematurely.
