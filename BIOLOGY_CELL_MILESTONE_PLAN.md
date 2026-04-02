# Plan: Next iteration after chemistry (single-cell biology milestone)

## Where things stand

The **chemistry milestone is complete** (`CHEMISTRY_MILESTONE_PLAN.md`). You have:

- A standalone **`chemistry.py`**: elements, energy constants, `Universe`, greedy assembly, finalization with energy checks, byte accounting, `MOLECULE_TARGETS`, and JSON-friendly snapshots via `big_bang(..., emit_line=...)`.
- A thin **`smallthings.py`** CLI that runs chemistry and still holds a **stub `Cell`**: **`photosynthesis`** is invalid (wrong `self`, wrong `molecules` shape), and **`ingest`** mutates a list while iterating by index (**`pop(i)`** skips elements).

`intent.md` names the next meaningful slice of progress explicitly:

> *“Getting a single cell to form and metabolize and eventually die is tremendous progress.”*

It also says **biology should depend on chemistry** (import the chemistry module), **nothing from thin air**, and **death should return matter toward an elemental / decomposed picture**—not erase bytes. **2D space, wall-clock time, DNA, and multi-cellular plants** remain **out of scope** for this milestone.

---

## Milestone: one honest cell on top of chemistry

Goal: a **minimal, debuggable “biology” layer**—**one cell** (or a tiny population later if trivial)—that **moves existing bytes** between the chemical universe and internal storage, **spends energy** for simple processes, and **can die** with **storage returned** to a pool the chemistry layer understands (e.g. `free_atoms` or an explicit “detritus” buffer), without inventing new atoms.

### 1. Module boundary (`biology.py`)

- Add **`biology.py`** that **imports `chemistry`** only (no circular imports).
- **Move** the real `Cell` implementation out of **`smallthings.py`** into **`biology.py`**. Keep **`smallthings.py`** as the **entrypoint** that can run **chemistry-only** (current behavior) and optionally a **small “cell demo”** subcommand or script path once the cell exists.
- Reserve **`photosynthesis`** for a **later** milestone unless you add a **trivial, energy-balanced** stub that does not reference undefined globals.

### 2. Environment contract (how the cell sees the world)

- Define a small **“environment” or `World` view”**: references to **`Universe`** (or subsets: `free_atoms`, completed `molecules`, maybe partials—pick the **smallest** surface that stays honest).
- **Invariant**: the cell **never creates** bytes; it only **requests moves** from shared buffers (same spirit as chemistry accounting).
- Decide **v1 feeding source**: e.g. **only `free_atoms`**, or **free_atoms + completed small molecules**—document the choice in one place (docstring on the feeder function).

### 3. Fix `ingest` (correctness first)

- Replace **index + `pop` while iterating** with a **safe pattern** (iterate a copy, collect indices to remove, or build new lists).
- **Clarify types**: **`bytearray`** vs **`list`** of length-1 **`bytes`**—pick one and use it consistently with `get_type` from **`chemistry`**.
- **`targets`**: keep as a set/list of **`Elem`**; ingestion respects **energy** if you charge per atom or per bond broken when “unpacking” (optional in v1).

### 4. Minimal metabolism (v1)

- Add **one or two simple rules**, not a full pathway library. Examples (choose what fits the existing `Universe` shape):
  - **Passive uptake**: per tick, move up to **N** bytes from `free_atoms` into `storage` if **`Elem`** matches targets and **energy** ≥ cost.
  - **Simple transformation** (optional): e.g. spend energy to “use” one completed `(kind, payload)` molecule and return products into **`free_atoms`** using **only bytes already in the payload** (no new random bytes).
- **Energy**: either a **per-cell pool** or **shared universe energy**—pick one and document. Intent allows drastic simplification; prefer **one global knob** or **cell-local** but not both until needed.

### 5. Death and decomposition

- **Death condition** (pick one for v1): **max age** (tick count), **energy below threshold**, or **storage empty for M ticks**—whatever is easiest to observe in logs.
- **On death**: append **every byte** from **`cell.storage`** back into **`Universe.free_atoms`** (or a dedicated **return buffer** merged into `free_atoms` in one step). Optional: credit **`ENERGY_RELEASE_BREAK`**-style energy to the universe when “breaking” notional internal bonds—only if it stays easy to reason about.
- **Re-run accounting** or assert: **total atoms** in universe + cell still matches the **original** input count when running a closed scenario (recommended test harness).

### 6. Observability (extend the harness)

- Reuse the **JSON line** pattern: add **cell fields** (`age`, `energy`, `storage_len`, maybe **Elem counts**) on the same timeline as chemistry batch/final logs, or a **separate `phase`** string (e.g. `"cell_tick"`).
- CLI: optional **ticks**, **cell starting energy**, **verbosity**—mirror the chemistry flags so you can replay.

### 7. Stop before (same spirit as chemistry milestone 6)

- **No** 2D grid placement, **no** wall-clock–driven sim loop as the primary model (a discrete **for tick in range(T)** loop is fine).
- **No** DNA, reproduction, or multi-cellular structure.
- **No** pygame / browser **required** for “done”—text/JSON is enough.

---

## Order of work (suggested)

1. **Add `biology.py`**, move **`Cell`** from **`smallthings.py`**, import **`chemistry`**.
2. **Define environment API** (what the cell can read/consume from **`Universe`**).
3. **Rewrite `ingest`** (safe iteration + consistent buffer types).
4. **Metabolism v1** (uptake and/or one transformation) with **energy checks**.
5. **Death + decomposition** back into **`free_atoms`** (or documented equivalent).
6. **Logging + CLI** hooks for cell state; optional tiny **closed test** (fixed byte sequence, assert counts).
7. **Stop** before 2D, real-time coupling, photosynthesis complexity, DNA, or plants.

---

## Success criteria for this milestone

You can point to a run (or test) where:

- **`ingest` / uptake** does not skip or corrupt bytes due to iteration bugs.
- The cell **only moves** bytes that already exist in the shared state; **no silent creation** of new atom bytes.
- **Metabolism** can **consume energy** (or refuse action when energy is insufficient).
- The cell **can die**, and afterward **all** of its stored bytes are **accounted for** in the elemental / free pool again (plus chemistry invariants still hold if you combine both layers in one scenario).
- A human can **follow** behavior from **structured logs** without attaching a GUI.

That matches **`intent.md`**’s ordering—chemistry solid, then **one cell** with a believable life cycle—while keeping the **garden / 2D / DNA** vision safely later.
