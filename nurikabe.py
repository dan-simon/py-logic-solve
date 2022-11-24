from z3 import Int, And, If, Not, Or, Solver, is_true
from lib import set_problem, parse_int_grid, all_2x2, all_neighbors, at, connected, \
construct_vars, eq, inds, shaded_vars
import time

g = parse_int_grid('''
I.5....4..3.6..........1
........................
..............1...1.....
.......6..............1.
..1.......1............6
......1.......A.4...6...
5..........4............
.....4.......5..........
...2.....8..............
.......1.......2........
............2...3.......
...3......5.........H...
.................4....6.
.1...3.4................
''', exc='?')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

# The shaded cells are connected
root = Int('r1'), Int('r2')

clues = [i for i in inds() if at(g, i) != None]

cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: eq(root, x)), 'uc')[0]

# Regions of unshaded cells (one per clue)
rs = construct_vars(Int, 'r', (height, width))

# Each region of unshaded cells must all connect to its clue
cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: at(rs, x) == clues.index(x) if x in clues else False), 'c')[0]

# Check if clue at i is in range of cell at j
in_range = lambda i, j: sum(abs(k1 - k2) for (k1, k2) in zip(i, j)) < at(g, i) or at(g, i) == -1

# Straightforwardly compute number of black squares in each region, by summing
cons += [sum(If(And(Not(at(shaded, i)), at(rs, i) == ind), 1, 0) for i in inds() if in_range(j, i)) == at(g, j)
for (ind, j) in enumerate(clues) if at(g, j) != -1]

# Cells can each only be part of certain (close enough) clues
cons += [Or(at(shaded, i), *[at(rs, i) == ind for (ind, j) in enumerate(clues) if in_range(j, i)]) for i in inds()]

# Clues cannot be shaded
cons += [Not(at(shaded, i)) for i in clues]

# Clues must be part of their regions
cons += [at(rs, i) == ind for (ind, i) in enumerate(clues)]

# Adjacent unshaded neighbors must be in same region
cons += all_neighbors(lambda x, y: Or(at(shaded, x), at(shaded, y), eq(at(rs, x), at(rs, y))))

# No 2x2 is fully shaded
cons += all_2x2(lambda *a: Not(And(*(at(shaded, i) for i in a))))

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
