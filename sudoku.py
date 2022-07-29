from z3 import Int, And, Distinct, Solver, is_true
from lib import set_problem, parse_int_grid, at, construct_vars, inds, only, write_int
import time

g = parse_int_grid('''
.23.164..
...8....9
6.......2
1...3..2.
7..1.8..5
.8..9...1
2.......7
9....1...
..657.24.
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Construct the 9 3x3 regions
regions = [[(3 * i1 + j1, 3 * i2 + j2) for j1 in range(3) for j2 in range(3)] for i1 in range(3) for i2 in range(3)]

# height, width, the number of regions, and the size of each region should all be the same
assert height == width == len(regions) == only(list({len(i) for i in regions}))

vals = construct_vars(Int, 'n', (height, width))

# Values must be between 1 and 9
cons += [And(1 <= j, j <= height) for i in vals for j in i]

# Different values in rows
cons += [Distinct(*i) for i in vals]

# Different values in columns
cons += [Distinct(*i) for i in zip(*vals)]

# Different values in regions
cons += [Distinct(*(at(vals, j) for j in i)) for i in regions]

# Clues are satisfied
cons += [at(vals, i) == at(g, i) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join(write_int(m[j].as_long()) for j in i) for i in vals))
