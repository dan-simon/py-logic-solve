from z3 import Int, And, Or, Solver, is_true
from lib import set_problem, parse_int, to_grid, at, inds, shaded_vars
import time

# Nonograms with this input format are a bit nontrivial to parse
def parse(g, clue_h, clue_w):
    t = to_grid(g)
    # Clues at top of columns (for columns)
    v_clues = [[parse_int(t[i][j]) for i in range(clue_h) if t[i][j] not in '.#X0'] for j in range(clue_w, len(t[0]))]
    # Clues at left of rows (for rows)
    h_clues = [[parse_int(t[i][j]) for j in range(clue_w) if t[i][j] not in '.#X0'] for i in range(clue_h, len(t))]
    # Given cells in the nonogram itself
    t = [[True if j in 'xX#1' else (False if j in 'oO0' else None) for j in i[clue_w:]] for i in t[clue_h:]]
    return v_clues, h_clues, t

v_clues, h_clues, g = parse('''
XXX.......1.....
XXX..224.11..11.
XXX.31524115.313
XXX334214444B263
..2.............
112.............
331.............
422.............
261.............
124.............
.44.............
114.............
412.............
421.............
.28.............
.26.............
..7.............
..3.............
''', 4, 3)

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

# We can't use construct_vars for the below because rows and columns have different numbers of clues
# from each other.

# Where each column clue starts and ends (row numbers; first/last shaded cells)
v_bounds = [[(Int('vbs-' + str(ind1) + '-' + str(ind2)), Int('vbe-' + str(ind1) + '-' + str(ind2)))
for ind2 in range(len(i))] for (ind1, i) in enumerate(v_clues)]

# Where each row clue starts and ends (column numbers; first/last shaded cells)
h_bounds = [[(Int('hbs-' + str(ind1) + '-' + str(ind2)), Int('hbe-' + str(ind1) + '-' + str(ind2)))
for ind2 in range(len(i))] for (ind1, i) in enumerate(h_clues)]

# The start-end differences must be the right size
cons += [k - j == c - 1 for i in list(zip(v_bounds, v_clues)) + list(zip(h_bounds, h_clues)) for ((j, k), c) in zip(*i)]

# Each end must be at least 2 before the next start (so that there's an empty cell in between)
cons += [j + 1 < k for i in v_bounds + h_bounds for ((_, j), (k, _)) in zip(i[:-1], i[1:])]

# All starts/ends must be greater than 0
cons += [i[0][0] >= 0 for i in v_bounds + h_bounds if i]

# All starts/ends must be less than height/width
cons += [i[-1][1] < b for (i, b) in [(k, height) for k in v_bounds] + [(k, width) for k in h_bounds] if i]

# The starts/ends on a column actually tell us which cells are shaded in that column
cons += [at(shaded, i) == Or(*[And(j[0] <= i[0], i[0] <= j[1]) for j in v_bounds[i[1]]]) for i in inds()]

# The starts/ends on a row actually tell us which cells are shaded in that row
cons += [at(shaded, i) == Or(*[And(j[0] <= i[1], i[1] <= j[1]) for j in h_bounds[i[0]]]) for i in inds()]

# If there are given cells in the grid, we have to follow those too.
cons += [at(shaded, i) == at(g, i) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
