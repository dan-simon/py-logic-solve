from z3 import Int, And, Not, Or, Solver, is_true
from lib import set_problem, parse_int_grid, ExactlyOne, all_2x2, at, connected, \
eq, in_bounds, inds, minus, neighbors, plus, shaded_vars, times
import time

g = parse_int_grid('''
.........5.....
.......3......X
..X.........4..
3....4.........
...X......2....
........3......
.............X.
...4.......2...
.X.............
......3........
....X......2...
.........4....3
..2.........3..
X......2.......
.....X.........
''', exc={'X': -1})

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# set up a shading
shaded = shaded_vars('s')

# root of the unshaded cells (which must be connected)
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

# No 2x2 can be all one thing
cons += all_2x2(lambda *a: And(Or(*[at(shaded, i) for i in a]), Or(*[Not(at(shaded, i)) for i in a])))

# Any unshaded cell without clues must have at least two unshaded neighbors
cons += [Or(at(shaded, i), Not(ExactlyOne(Not(at(shaded, j)) for j in neighbors(i)))) for i in inds() if at(g, i) == None]

# Add conditions for clue cells with no number...
cons += [And(Not(at(shaded, i)), ExactlyOne(Not(at(shaded, j)) for j in neighbors(i))) for i in inds() if at(g, i) == -1]

follow = lambda i, j, k: plus(i, times(k, minus(j, i)))

# ...and, with more difficulty, for clue cells with numbers.
# Our approach here is to consider each option for a direction the clue could extend in.
# For each such option, there are three types of contraints:
# (1) None of the cells in that direction can be shaded
# (2) All the other neighbors not in that direction must be shaded
# (3) The cell at distance (clue number) in that direction, if it exists, must be shaded
cons += [And(Not(at(shaded, i)), Or(
*[And(*[Not(at(shaded, follow(i, j, k))) for k in range(1, at(g, i))],
*[at(shaded, k) for k in neighbors(i) if k != j],
*([at(shaded, follow(i, j, at(g, i)))] if in_bounds(follow(i, j, at(g, i))) else []))
for j in neighbors(i) if in_bounds(follow(i, j, at(g, i) - 1))]
)) for i in inds() if at(g, i) not in (None, -1)]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
