from z3 import Int, And, Not, Or, Solver, is_true
from lib import set_problem, parse_regions, all_2x2, all_neighbors, at, connected, \
construct_vars, eq, get_rtable, positioning, shaded_vars
import time

# Note: I think that for human solving, this LITS requires a decent amount of brute force.
regions, g = parse_regions('''
AAABBBCCDDDDEEFF
AAABGGCCDDDDFEEF
HHHBBGGCCFFFFEEF
HIIIBBGGCCFFEEFF
HKIILBBGGCCFFFFJ
KKILLLBBGGCCJJFJ
KLLLMLLBBGGNNJJJ
KKLLMMMOOOGONJNN
MMMMMMMMMOOONNNN
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# LITS shapes (non-square tetrominos, as lists of positions)
lits_shapes = [((0, 0), (0, 1), (0, 2), (0, 3)), ((0, 0), (0, 1), (0, 2), (1, 0)),
((0, 0), (0, 1), (0, 2), (1, 1)), ((0, 0), (0, 1), (1, 1), (1, 2))]

# all LITS shape positions in the grid, together with which shape they are (ind)
lits_shapes = [(ind, j) for (ind, i) in enumerate(lits_shapes) for j in positioning(i)]

rtable = get_rtable(regions)

# Group tetrominos by region they're fully in (eliminating all those split between regions)
def group_by_region(x):
    r = [[] for _ in range(len(regions))]
    for i in x:
        if len({rtable[j] for j in i[1]}) == 1:
            r[rtable[i[1][0]]].append(i)
    return r

cons = []

shaded = shaded_vars('s')

# Standard root-connected setup
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: eq(root, x)), 'a')[0]

# table of shape type for each region (as number)
ty = construct_vars(Int, 't', (len(regions),))

# Each region must have some LITS shape
cons += [Or(*[And(ty[ind] == p1, *[at(shaded, v) == (v in p2) for v in i]) for (p1, p2) in j])
for (ind, (i, j)) in enumerate(zip(regions, group_by_region(lits_shapes)))]

# Two different regions with adjacent shaded cells cannot have the same LITS shape
cons += all_neighbors(lambda i, j: Not(And(rtable[i] != rtable[j], at(shaded, i), at(shaded, j), ty[rtable[i]] == ty[rtable[j]])))

# No 2x2 can be fully shaded.
cons += all_2x2(lambda *a: Or(*[Not(at(shaded, i)) for i in a]))

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
