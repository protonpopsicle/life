#!/usr/bin/env python3

import pprint
from enum import Enum

Elem = Enum('Elem', ['C', 'H', 'O', 'N', 'METAL', 'SOFT_SOLID',
                     'CODE_A', 'CODE_B', 'CODE_C', 'CODE_D', 'CODE_E'])

molecules = {
    'oxygen': (Elem.O, Elem.O),
    'carbon_dioxide': (Elem.C, Elem.O, Elem.O),
    'water': (Elem.H, Elem.H, Elem.O),
    # Endogenous d-glucose - C6H12O6, building block for cellulose
    'glucose': (Elem.C, Elem.C, Elem.C, Elem.C, Elem.C, Elem.C, Elem.C,
                Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H,
                Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H, Elem.H,
                Elem.O, Elem.O, Elem.O, Elem.O, Elem.O, Elem.O, Elem.O),
}

class Cell:
    species = "Canis familiaris"

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

with open("smallthings.py", mode='rb') as file:
    raw_data = file.read()

nutribytes = bytearray(raw_data)

def get_type(nb):
    _index = nb % len(Elem) + 1
    return Elem(_index)

def analyze(nutribytes):
    result = {elem: 0 for elem in Elem}
    for nb in nutribytes:
        result[get_type(nb)] += 1
    return result

print(cell)
pprint.pp(analyze(nutribytes))
cell.ingest(nutribytes, [Elem.METAL])
pprint.pp(analyze(cell.storage))
