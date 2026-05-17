# Plan: Closed accounting for CO2, H2O, and O2

## Goal

In the bio simulation, molecules **CO2**, **H2O**, and **O2** in the environment should never be created or destroyed net across the full lifecycle: cells appear, live, die, decompose, and when nothing organic remains, **`CO2Count`**, **`H2OCount`**, and **`O2Count`** should match their initial values** from [`bio-web/environment.js`](../bio-web/environment.js).

Observed drift after a full run (example): `CO2` and `H2O` both increased by the same amount; `O2` increased more. That pattern matches **stoichiometry / bookkeeping bugs** (wrong coefficients, missing O2 on oxidation, fixed glucose counts that do not match cellulose lost), not random simulation noise.

---

## Why this is a software issue

If every operation were the **inverse** of a consistent reaction step (same multipliers, O2 included where fixation/oxidation require it), and cellulose were built and torn down with **matching** glucose equivalents, then after all cells and organic stores are gone the environment triple should return to its initial vector (up to floating-point error if fractional steps are used).

---

## Root cause 1: O2 produced in photosynthesis but not consumed when organic matter becomes CO2 + H2O

**Photosynthesis** (simplified balanced form per glucose):

- 6 CO₂ + 6 H₂O → C₆H₁₂O₆ + 6 O₂

[`bio.js`](../bio-web/bio.js) removes CO₂/H₂O and adds O₂ in line with that for the batch size used in `photosynthesis`.

**Respiration** and **`decomposeGlucose`** only add:

- organic (glucose) → +6n CO₂ and +6n H₂O

They **never subtract O₂**. The reverse of photosynthesis for full oxidation is:

- C₆H₁₂O₆ + 6 O₂ → 6 CO₂ + 6 H₂O

So every full cycle **photosynthesis → respiration or decomposition** leaves **+6 O₂ per glucose** in the current ledger. That explains **O₂ rising** while CO₂/H₂O behavior can be further skewed by other bugs.

**Fix:** For every pathway that converts stored glucose (or glucose equivalent) back to CO₂ + H₂O, **also subtract the matching O₂** (same 6× coefficient per glucose unit in this simplified model). Apply consistently in:

- `respiration`
- `decomposeGlucose` (or its callers)

If you ever want anaerobic pathways without O₂, you cannot also emit full 6 CO₂ + 6 H₂O per glucose without breaking this closed-loop invariant.

---

## Root cause 2: Cell wall breakdown uses a full `GLC_TO_MAKE_CELLULOSE` per tick but only removes 0.5 cellulose

In `microbialUpdate`, wall processing does something equivalent to:

- emit decomposition products for **`GLC_TO_MAKE_CELLULOSE`** glucose equivalents
- then `cellWall.cellulose -= 0.5`

`biosynthesis` spends **`GLC_TO_MAKE_CELLULOSE` glucose to add +1 cellulose**. Tearing down wall mass must return **the same glucose equivalent per unit cellulose** removed.

If only **0.5** cellulose is lost per tick, CO₂/H₂O (and O₂, after root cause 1 is fixed) should scale by **`0.5 * GLC_TO_MAKE_CELLULOSE`**, not **`1 * GLC_TO_MAKE_CELLULOSE`** every tick. As written, that step can inject roughly **2×** the CO₂/H₂O it should per wall loss — consistent with CO₂ and H₂O rising **together**.

**Fix:**

- Define one constant, e.g. treat `GLC_TO_MAKE_CELLULOSE` as **glucose per cellulose unit** everywhere.
- On wall loss: `oxidizeGlucoseEquivalent(environment, deltaCellulose * GLC_TO_MAKE_CELLULOSE)` (today `deltaCellulose = 0.5`).
- Avoid duplicating the literal `200` in the decomposer; use the same constant as biosynthesis.

---

## Root cause 3: Initial cellulose without paying the glucose “invoice”

Cells start with `cellulose: 1` without spending `GLC_TO_MAKE_CELLULOSE` glucose. When the corpse is fully decomposed, the sim can return **more** CO₂/H₂O/O₂ than was ever withdrawn for that first polymer in your economy.

**Fix (pick one and document it):**

- **A.** Start with `cellulose: 0` (and acceptable visuals), or  
- **B.** Track **paid** cellulose vs seed (only decompose returns for paid units), or  
- **C.** Charge construction at birth (usually undesirable).

Minimal: **start at 0** or only run decomposition returns for cellulose that was actually created via `biosynthesis`.

---

## Root cause 4: ATP and other internal sinks

ATP is created in `respiration` and spent in `repair`, `biosynthesis`, movement, etc., without returning atoms to the environment. That is consistent with the CO₂/H₂O/O₂ invariant **as long as** ATP is not modeled as containing C/H/O drawn from those pools. No change required for the stated goal unless the energy model later couples to those counts.

---

## Implementation plan (minimal)

1. **Centralize stoichiometry** in [`chem.js`](../bio-web/chem.js) or a small module used by [`bio.js`](../bio-web/bio.js), e.g.:
   - helpers that apply **paired** deltas: forming one glucose from env vs oxidizing one glucose back to env (mirror coefficients, including **O₂** on oxidation).

2. **Refactor `photosynthesis`** to use the fixation helper (optional cleanup; logic already mostly correct for CO₂/H₂O/O₂ per batch).

3. **Refactor `respiration` and `decomposeGlucose`** to use the oxidation helper: **+6n CO₂, +6n H₂O, −6n O₂** per n glucose equivalents.

4. **Fix `microbialUpdate` wall branch** to use **`deltaCellulose * GLC_TO_MAKE_CELLULOSE`** (not a full `GLC_TO_MAKE_CELLULOSE` per 0.5 step).

5. **Fix initial cellulose** so decomposition never returns mass that was never debited.

6. **Dev sanity check** (optional): snapshot env counts after `init()`; when particle list has no cells / no organic mass, assert counts equal initial (within epsilon if using floats).

---

## Verification ideas

- Run with **`light: 0`** to freeze photosynthesis; exercise only respiration/decomposition paths and check invariants.
- Full run with light on; assert env triple after full teardown matches initial.

---

## References in codebase

- Environment defaults: [`bio-web/environment.js`](../bio-web/environment.js)
- Metabolism and decomposition: [`bio-web/bio.js`](../bio-web/bio.js)
- Placeholder chemistry: [`bio-web/chem.js`](../bio-web/chem.js)
