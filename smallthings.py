#!/usr/bin/env python3

"""simple ruleset:
1. bytes are immutable and cannot change value
2. bytes cannot be copied or destroyed (b/c they're "atoms")
3. bytes can be grouped in different structures (as in "bonded")
4. forming a bond consumes energy, breaking a bond releases energy
"""

import sys
import pprint
from enum import Enum

# the most common elements in living organisms
# all bytes read into the program will be mapped to these elements
Elem = Enum('Elem', ['C', 'H', 'O', 'N', 'P', 'S'])

# molecular_recipe = {
#     'O2':  bytearray([Elem.O, Elem.O]),
#     'CO2': bytearray([Elem.C, Elem.O, Elem.O]),
#     'H2O': bytearray([Elem.H, Elem.H, Elem.O]),
#     # Endogenous d-glucose - C6H12O6, building block for cellulose
#     'glucose': bytearray([Elem.C, Elem.C, Elem.C, Elem.C, Elem.C, Elem.C, Elem.C,
#                           Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H,
#                           Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H,
#                           Elem.O, Elem.O, Elem.O, Elem.O, Elem.O, Elem.O, Elem.O]),
# }

class Cell:
    def __init__(self, name='bob', age=0):
        self.name = name
        self.age = age
        self.size = 0
        self.storage = bytearray()

    def __str__(self):
        return f"{self.name}({self.age})"

    def photosynthesis(light, water, carbon_dioxide):
        return molecules['glucose'], molecules['oxygen']

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

def get_info(bytes_collection):
    return "".join([Elem(x % len(Elem) + 1).name for x in bytes_collection])

def get_type(byte):
    _index = int.from_bytes(byte, byteorder=sys.byteorder) % len(Elem) + 1
    return Elem(_index)

def big_bang():
    molecules = []
    o2_partials = []
    co2_partials = []
    h2o_partials = []
    free_atoms = bytearray()

    with open("input.pdf", "rb") as f:
        byte = f.read(1)
        while byte != b"":
            _type = get_type(byte)
            if _type == Elem.C:
                # handle Carbon
                co2_partials.append(bytearray(byte))
            elif _type == Elem.H:
                # handle Hydrogen
                found = False
                for partial in h2o_partials:
                    if len(partial) == 1:
                        partial += byte
                        found = True
                        break

                if not found:
                    h2o_partials.append(bytearray(byte))
            elif _type == Elem.O:
                # handle Oxygen
                found = False
                for partial in h2o_partials:
                    if len(partial) == 2:
                        partial += byte
                        found = True
                        break

                if found:
                    continue

                for partial in co2_partials:
                    if len(partial) < 3:
                        partial += byte
                        found = True
                        break

                if found:
                    continue

                for partial in o2_partials:
                    if len(partial) == 1:
                        partial += byte
                        found = True
                        break
    
                if not found:
                    o2_partials.append(bytearray(byte))

            byte = f.read(1)

    pprint.pp({'O2':  [get_info(partial) for partial in o2_partials]})
    pprint.pp({'CO2': [get_info(partial) for partial in co2_partials]})
    pprint.pp({'H2O': [get_info(partial) for partial in h2o_partials]})

# def ingest(nutribytes, dest, targets):
#     feeding = True
#     while feeding:
#         feeding = False
#         for i, nb in enumerate(nutribytes):
#             if get_type(nb) in targets:
#                 dest.append(nutribytes.pop(i))
#                 feeding = True
#                 break

# print(cell)
# pprint.pp(analyze(nutribytes))
# molecules.append(build_molecule(nutribytes, molecular_recipe['O2']))
# molecules.append(build_molecule(nutribytes, molecular_recipe['CO2']))
# molecules.append(build_molecule(nutribytes, molecular_recipe['H2O']))

# for molecule in molecules:
#     pprint.pp(analyze(molecule))
# cell.ingest(nutribytes, [Elem.O])
# pprint.pp(analyze(cell.storage))
if __name__ == "__main__":
    big_bang()

