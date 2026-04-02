#!/usr/bin/env python3

"""simple ruleset:
1. bytes are immutable and cannot change value
2. bytes cannot be copied or destroyed (b/c they're "atoms")
3. bytes can be grouped in different structures (as in "bonded")
4. forming a bond consumes energy, breaking a bond releases energy
"""

import argparse
import json

from chemistry import INITIAL_ENERGY, big_bang, get_type


class Cell:
    def __init__(self, name="bob", age=0):
        self.name = name
        self.age = age
        self.size = 0
        self.storage = bytearray()

    def __str__(self):
        return f"{self.name}({self.age})"

    def photosynthesis(light, water, carbon_dioxide):
        return molecules["glucose"], molecules["oxygen"]

    def ingest(self, nutribytes, targets):
        feeding = True
        while feeding:
            feeding = False
            for i, nb in enumerate(nutribytes):
                if get_type(nb) in targets:
                    self.storage.append(nutribytes.pop(i))
                    feeding = True
                    break


raw_data = None
cell = Cell()
molecules = []


def _emit_json_line(obj):
    print(json.dumps(obj, separators=(",", ":")), flush=True)


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Byte stream → elements → greedy partials; finalize with energy."
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
        help=f"Initial energy pool (default: {INITIAL_ENERGY})",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Pretty-print partials and summary tables after the final JSON line",
    )
    p.add_argument(
        "--log-every",
        type=int,
        default=0,
        metavar="N",
        help="Emit one JSON log line every N bytes read (phase=batch)",
    )
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    u = big_bang(
        args.input,
        initial_energy=args.energy,
        log_every_n_bytes=args.log_every,
        verbose=args.verbose,
        emit_line=_emit_json_line,
    )
    molecules = u.molecules
