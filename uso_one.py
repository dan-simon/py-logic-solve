from z3 import Int, Not, Or, PbEq, Solver, is_true
from lib import set_problem, parse_regions, parse_int_grid, ExactlyOne, \
all_neighbors, at, connected, eq, inds, neighbors, shaded_vars
import time

regions = parse_regions('''
AAAAAAABBB
CAACAADDDB
CCCCEEDFDF
GGEEEEHFFF
GGEEHHHFFF
GGGGHHHFFF
IIJGHHHKFK
IIJJLLLKKK
IIIJLLLLKK
IIIJLLKKKK
''', grid=False)

g = parse_int_grid('''
.2.2..2..0
........1.
0...3....1
..13.0.2..
1.....2...
.3.......2
...3......
..0.......
..1...2.31
...2...2..
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

root = Int('r1'), Int('r2')

# The unshaded cells are connected (to some root)
cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

# No two adjacent cells are shaded
cons += all_neighbors(lambda x, y: Or(Not(at(shaded, x)), Not(at(shaded, y))))

# Clues are not shaded
cons += [Not(at(shaded, i)) for i in inds() if at(g, i) != None]

# Exactly one clue in each region ("for i in r if at(g, i) != None") is incorrect.
cons += [ExactlyOne(Not(PbEq([(at(shaded, j), 1) for j in neighbors(i)], at(g, i)))
for i in r if at(g, i) != None) for r in regions]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
