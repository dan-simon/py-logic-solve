from z3 import Bool, And, Or, PbEq, Solver, is_true
from lib import set_problem, parse_int_grid, at, construct_vars, eq, in_bounds, inds, neighbors
import time

g = parse_int_grid('''
.....X....
..........
0.........
.1.....1..
....X.....
..........
.X..1..1..
.....1....
..........
..........
''', exc='X')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# The general format here is that a space is represented by five variables, the first four of which are whether
# its top quadrant, right quadrant, bottom quadrant, and left quadrant, in that order, are shaded,
# and the fifth of which is "is this space all shaded or all unshaded". We then write functions
# to get the shading around intersections and to determine which shadings around intersections are valid.
# This is the slowest genre of those here, with it sometimes taking over 5 seconds to set up the constraints
# (though actually solving from constraints takes 1 second usually, or less).

# Get valid shadings around intersections.
def get_valid_eights():
    p = [()]
    for i in range(8):
        p = [i + (j,) for i in p for j in (False, True)]
    return [i for i in p if (not any(i)) or all(len(k) in (0, 2, 4) for k in
    ''.join('01'[j] for j in i[i.index(True):] + i[:i.index(True)]).split('1'))]

# Get valid shadings of spaces (for non-clues). There are six; four triangles, plus no shading at all and fully shaded.
def get_valid_fours():
    return [(False, False, False, False, True), (False, False, True, True, False), (False, True, True, False, False),
    (True, False, False, True, False), (True, True, False, False, False), (True, True, True, True, True)]

v = lambda i, j: at(shadings, i)[j] if in_bounds(i) else True

# Get the shading around the intersection with (a, b) at its top left.
def read_around(a, b):
    return [v(i, j) for (i, j) in (((a, b), 2), ((a, b), 1), ((a, b + 1), 3), ((a, b + 1), 2),
    ((a + 1, b + 1), 0), ((a + 1, b + 1), 3), ((a + 1, b), 1), ((a + 1, b), 0))]

eights = get_valid_eights()

fours = get_valid_fours()

cons = []

# Create shadings
shadings = construct_vars(Bool, 's', (height, width, 5))

# Check that intersections are valid
cons += [Or(*[eq(read_around(i, j), k) for k in eights]) for i in range(-1, height) for j in range(-1, width)]

# Check that spaces are valid
cons += [Or(*[eq(at(shadings, i), j) for j in fours]) for i in inds()]

# Check that the only spaces that are fully shaded (all shading true) are clues, and that clues are fully shaded
cons += [And(*[at(shadings, i)]) == (at(g, i) != None) for i in inds()]

# Check that spaces have the right number of triangles around them (the last of the five shading properties
# can be thought of as "no triangle"; the negation ("*no* triangle") gives us the
# "len(neighbors(i)) - at(g, i))" rather than "at(g, i)").
cons += [PbEq([(v(j, 4), 1) for j in neighbors(i)], len(neighbors(i)) - at(g, i)) for i in inds() if at(g, i) not in (None, -1)]

# Output format is a bit weird. Period is unshaded and hashmark is fully shaded (clue), but 1-4 are triangles.

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.1234#'[fours.index(tuple(is_true(m[k]) for k in j))] for j in i) for i in shadings))
