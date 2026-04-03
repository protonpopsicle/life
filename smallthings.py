#!/usr/bin/env python3

"""simple ruleset:
1. bytes are immutable and cannot change value
2. bytes cannot be copied or destroyed (b/c they're "atoms")
3. bytes can be grouped in different structures (as in "bonded")
4. forming a bond consumes energy, breaking a bond releases energy

CLI: chemistry on a file; optional ``--cell-ticks`` JSON logs; ``--self-test`` invariant check.
"""

import argparse
import json
import pprint
import sys

from biology import (
    Cell,
    ChemEnvironment,
    Elem,
    cell_final_observation_row,
    cell_observation_row,
    closed_atom_count,
    closed_world_self_test,
)
from chemistry import INITIAL_ENERGY, big_bang

raw_data = None
cell = Cell()
molecules = []


def _emit_json_line(obj):
    print(json.dumps(obj, separators=(",", ":")), flush=True)


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Byte stream → chemistry; optional cell metabolism JSON logs."
    )
    p.add_argument(
        "input",
        nargs="?",
        default="input.pdf",
        help="Input file path (default: %(default)s)",
    )
    p.add_argument(
        "--energy",
        type=int,
        default=None,
        metavar="N",
        help=f"Initial universe energy (default: {INITIAL_ENERGY})",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Pretty-print chemistry tables (and cell state after cell ticks)",
    )
    p.add_argument(
        "--log-every",
        type=int,
        default=0,
        metavar="N",
        help="Emit one JSON log line every N bytes read during chemistry (phase=batch)",
    )
    p.add_argument(
        "--cell-ticks",
        type=int,
        default=0,
        metavar="N",
        help="After chemistry, run N cell metabolism ticks (0 = chemistry only)",
    )
    p.add_argument(
        "--cell-max-age",
        type=int,
        default=None,
        metavar="N",
        help="Cell max_age_ticks (omit for immortal)",
    )
    p.add_argument(
        "--cell-max-uptake",
        type=int,
        default=8,
        metavar="N",
        help="Max free_atoms taken per metabolism tick (default: %(default)s)",
    )
    p.add_argument(
        "--cell-name",
        default="bob",
        help="Cell name for logs (default: %(default)s)",
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Run closed-world conservation check and exit (no input file)",
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    if args.self_test:
        try:
            closed_world_self_test()
        except AssertionError as e:
            _emit_json_line({"phase": "self_test", "ok": False, "error": str(e)})
            sys.exit(1)
        _emit_json_line({"phase": "self_test", "ok": True})
        sys.exit(0)

    u = big_bang(
        args.input,
        initial_energy=args.energy,
        log_every_n_bytes=args.log_every,
        verbose=args.verbose,
        emit_line=_emit_json_line,
    )
    molecules = u.molecules

    if args.cell_ticks > 0:
        sim_cell = Cell(name=args.cell_name, max_age_ticks=args.cell_max_age)
        env = ChemEnvironment(u)
        uptake_targets = list(Elem)
        ticks_done = 0
        for i in range(args.cell_ticks):
            if not sim_cell.alive:
                break
            meta = env.metabolism_tick(
                sim_cell,
                uptake_targets,
                max_uptake=args.cell_max_uptake,
            )
            _emit_json_line(
                cell_observation_row(
                    u, sim_cell, tick_index=i, metabolism=meta
                )
            )
            ticks_done = i + 1
        _emit_json_line(
            cell_final_observation_row(u, sim_cell, ticks_run=ticks_done)
        )
        if args.verbose:
            pprint.pp(
                {
                    "cell_verbose": {
                        "closed_atom_count": closed_atom_count(u, sim_cell),
                        "free_atoms": len(u.free_atoms),
                        "molecules": len(u.molecules),
                    }
                }
            )
