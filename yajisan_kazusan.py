from z3 import Int, If, Not, Or, Solver, is_true
from lib import set_problem, deep_map, parse_int, to_dir, to_grid, \
all_neighbors, at, connected, eq, inds, look, shaded_vars
import time

def parse(g):
    return deep_map(lambda x: ((parse_int(x[0]), to_dir(x[1], num=True))
    if x != '..' else None), to_grid(g, section_size=2), depth=2)

g = parse('''
....1>2>3>..........
..............2<....
....................
..........4v3v2v....
..2^................
..2^................
..2^................
4^..................
3^..2^..............
2^....2^5^5^..1^5^5^
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

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

cons += all_neighbors(lambda x, y: Or(Not(at(shaded, x)), Not(at(shaded, y))))

# Count shaded cells in a direction
c, vis = look((lambda pos, d, edge, n, v: 0 if edge else v + If(at(shaded, n), 1, 0)), Int, 'v')
cons += c

# Require clues to either be shaded or satisfied
cons += [Or(at(shaded, i), at(vis[at(g, i)[1]], i) == at(g, i)[0]) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))

