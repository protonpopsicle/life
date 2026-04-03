# Physics Requirements

## High-level description

The physical environment of the simulation is a garden, which is the whole universe.

### Time

Time within the simulation passes continuously, like in a videogame. Time can be manipulated for debugging purposes (start, stop, rate change).

### Space

The garden is 2 dimensional, represented in a two-dimensional plane. Space is not simulated at the microscopic level. Very small objects such as atoms, molecules and simple organisms are considered to occupy an area of the 2D grid but are not explicitly tracked within it. This containing grid square is a configurable division of the overall universe size.

### Gravity

At the bottom of the garden is a hard ground. gravity pulls everything towards the ground that is not supported by a rigid structure such as plant tissues.

### The sun

Light radiates from the top of the universe down towards the bottom. It is abundant and infinite.