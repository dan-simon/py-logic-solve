from z3 import Int, And, Not, Or, PbEq, Solver, is_true, If, Sum
from lib import set_problem, parse_regions, parse_clues, at, connected, eq, \
get_rtable, in_bounds, inds, plus, shaded_vars, times
import time

regions, g = parse_regions('''
AAAABCCCCCDDDDDDEE
AAFFBGGCCCDHHHHDEE
AAFFBGGCCCDHHHHDEE
BBBBBBBCCCDHHHHDEE
IJJCCCCCCCDHKKHDEL
IJJCCCCCCCDHKKHDEE
IIIMMMMMMMHHHHNNEE
OOOMPPPQHHHHHHHNEE
OOOMPPPQHHHHHNNNEE
MMMMPPPQQQQQHNEEEE
PPPPPPPPPPPQHNERRR
PPPPPPPPPPPQHNERRR
''')

clues = parse_clues('''
....2.....3.......
..2..2............
..................
..................
.2..........2....0
..................
...2..........2...
2......2..........
..................
..................
...............3..
..................
''', regions)



rtable = get_rtable(regions)

same_region = lambda i, j: rtable[i] == rtable[j]

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# Make a list of all runs of four (horizontally or vertically) adjacent positions
# (with the first and last positions, and thus all four, in bounds).
fours = [(i, plus(i, j), plus(i, times(j, 2)), plus(i, times(j, 3)))
for i in inds() for j in ((1, 0), (0, 1)) if in_bounds(plus(i, times(j, 3)))]

cons = []

shaded = shaded_vars('s')

# root of the shaded cells (which must be connected)
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: eq(root, x)), 'uc')[0]

# all four-cell runs must have at least one shaded cell, and must have at least one non-shaded cell
cons += [And(Or(*[at(shaded, i) for i in a]), Or(*[Not(at(shaded, i)) for i in a])) for a in fours]

# all clues must be satisfied
cons += [sum(If(at(shaded, j), 1, 0) for j in regions[i]) == v for (i, v) in clues]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))

