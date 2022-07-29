from z3 import Int, And, Implies, Not, PbEq, Solver, is_true
from lib import set_problem, parse_int_grid, all_2x2, at, connected, eq, inds, \
in_bounds, is_perimeter, orth_dir, plus, shaded_vars
import time

g = parse_int_grid('''
0..1312201.3223
0..1..........2
.1.322..2.1.323
...2..1.2.1.2..
3.22.3..231.221
22...233.21212.
....1..0.1.202.
.2.21333....221
......1.11.212.
2220.......10..
.....03..2.1...
2...02.2.2...03
212..22..2..12.
3..3...2....1.1
....2...02.3...
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# We treat slitherlink as a shading puzzle; as with cave, the area outside the loop is considered shaded

cons = []

shaded = shaded_vars('s')

# root of the unshaded cells (which must be connected)
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

# all shaded cells must be connected to the perimeter
cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: is_perimeter(x)), 'c')[0]

# no 2x2 checkerboards
cons += all_2x2(lambda a, b, c, d: Implies(And(at(shaded, a) == at(shaded, d), at(shaded, b) == at(shaded, c)),
at(shaded, a) == at(shaded, b)))

# for clues, number of different adjacent cells has to be clue number
# important note: cells outside the grid can count as adjacent (so we can't use neighbors
# because that doesn't include cells outside the grid)
cons += [PbEq([(Not(eq((at(shaded, plus(i, j)) if in_bounds(plus(i, j)) else True),
at(shaded, i))), 1) for j in orth_dir], at(g, i)) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))

