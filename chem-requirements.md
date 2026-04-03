# Chemistry Requirements

## High-level description

### Structures

#### Atomic elements

An atom is the smallest unit of an element that retains its chemical properties. In the simulation, real bytes of data are passed to the program as input. These bytes represent all available atoms in the universe. Bytes == atoms. Just as each byte in memory can represent a char, these bytes represent an atom of some element. The elements that exist in the simulation are: 

- Carbon (C)
- Hydorgen (H)
- Oxygen (O)
- Nitrogen (N)
- Phosphorus (P)
- Sulfur (S)

The choice of elements is based on the building blocks of biological life.

#### Molecules

A molecule is a discrete group of two or more atoms chemically bonded together in numbers defined exactly by the chemical formula. Molecules can be elements (consisting of only one kind of atom e.g. O₂) or they can be compounds consisting of atoms of different elements (e.g. H₂O). Which elements bond to form which molecules is defined as follows:

- O2: (2 Oxygen)
- CO2: (1 Carbon, 2 Oxygen)
- H2O: (E2 Hydrogen, 1 Oxygen) AKA water

### Processes

Energy is defined as the capacity to do work. It is measured in the unit of Joule (J).

In a chemical reaction, only the atoms present in the reactants can end up in the products. No new atoms are created, and no atoms are destroyed. In a chemical reaction, reactants contact each other, bonds between atoms in the reactants are broken, and atoms rearrange and form new bonds to make the products.

#### Chemical Bonding

Individual atoms form larger molecules through chemical bonding. In this simulation atoms bond to form molecules under 2 conditions:

1. Molecules are formed automatically due to underlying laws of attraction if the right combination of atoms is present.
2. Atoms separated by a great distance cannot link; So, they must be close enough together. Atoms have no size in this simulation but they do exist within a defined area (grid square).

Making bonds releases energy, therefore breaking bonds requires energy.