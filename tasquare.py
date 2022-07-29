from z3 import Int, If, Not, Or, Solver, is_true
from lib import set_problem, parse_int_grid, at, connected, construct_vars, \
eq, flatten, inds, look, neighbors, shaded_vars
import time

g = parse_int_grid('''
1..2......
.....3....
..5.......
.........4
......6...
.?........
....8.....
....9...??
.?........
.?...?....
''', exc='?')

# This function takes a list of values and returns a dictionary mapping
# number of neighbors of a tasquare clue and the total area of squares
# in those neighbors to list of options for sizes of those squares
# (including zero-size squares).
def get_table(x):
    # Calculate maximal value at most the square root of the highest clue
    v = max(int(i ** 0.5) for i in flatten(x) if i not in (None, -1))
    # Build up list of lists of tuples of n squares, for 0 <= n <= 4
    # (of numbers less than or equal to previously-mentioned maximal value)
    p = [[()]]
    for _ in range(4):
        p.append([i + (j,) for i in p[-1] for j in range(v + 1)])
    # Flatten to get a list of tuples of squares
    p = flatten(p, depth=2)
    # Tasquare rules actually let us do other stuff; specifically,
    # every cell has at least two neighbors, not all four squares can have nonzero area,
    # and only at most two can have area > 1. This gives a roughly 2% speedup.
    p = [i for i in p if len(i) >= 2 and sum(j > 0 for j in i) < 4 and sum(j > 1 for j in i) < 3]
    # Add each option to the table under the proper key
    t = {}
    for i in p:
        k = len(i), sum(j ** 2 for j in i)
        t.setdefault(k, [])
        t[k].append(i)
    return t

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# Construct a table of options for satisfying clues.
table = get_table(g)

cons = []

shaded = shaded_vars('s')

size = construct_vars(Int, 'z', (height, width))

clues = [i for i in inds() if at(g, i) != None]

# Make sure all the unshaded cells are connected (to the first clue)
cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(clues[0], x)), 'c')[0]

# Count shaded cells in each direction (counting the cell itself, if it's shaded)
c, vis = look((lambda pos, d, edge, n, v: If(at(shaded, pos), If(edge, 0, v) + 1, 0)), Int, 'v')
cons += c

# Make sure the horizontal number and vertical number is the same (this ensures square regions)
cons += [at(vis[0], i) + at(vis[2], i) == at(vis[1], i) + at(vis[3], i) for i in inds()]

# Set variables for the height (or equivalently width) of each shaded region
# (we need the -1 since we double-count the cell itself).
cons += [at(size, i) == If(at(shaded, i), at(vis[0], i) + at(vis[2], i) - 1, 0) for i in inds()]

# Make sure clues aren't shaded.
cons += [Not(at(shaded, i)) for i in clues]

# Make sure the sizes are in the above-constrcted table.
cons += [Or(*[eq([at(size, k) for k in neighbors(i)], j) for j in table[(len(neighbors(i)), at(g, i))]]) for i in clues if at(g, i) != -1]

# Make sure all the clues have some shaded neighbor.
cons += [Or(*[at(shaded, j) for j in neighbors(i)]) for i in clues if at(g, i) == -1]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))

