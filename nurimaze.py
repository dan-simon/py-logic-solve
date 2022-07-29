from z3 import And, Implies, Not, Or, Solver, is_true
from lib import set_problem, parse_regions, deep_map, to_grid, all_2x2, at, connected, \
eq, inds, is_perimeter, only, path, shaded_vars, some_edge
import time

def parse_clues(x):
    return deep_map(lambda j: j if j != '.' else None, to_grid(x), depth=2)

regions = parse_regions('''
...A.B...C
DD.A.B...C
.....B....
..........
.EE..F.G..
H....F.G..
HH...I.JKK
.....I.J..
.....L..MM
.....L....
''', periods=True, grid=False)

g = parse_clues('''
..o.o..t.t
......t...
....t....o
o..t...o..
......t...
...o.....o
......t...
o.o....t..
.S........
t.G...o.o.
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Get start and goal locations
tstart, tgoal = only([i for i in inds() if at(g, i) == 'S']), only([i for i in inds() if at(g, i) == 'G'])

# Set up a path from start to goal
c, edge_vars, start, goal = path(False, 'l')
cons += c

# Set up a shading
shaded = shaded_vars('s')

# Everything unshaded must connect to the start
cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(start, x)), 'ca')[0]

# Everything shaded must connect to the edge via diagonals (this is equivalent to having no unshaded loops)
cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: is_perimeter(x)), 'cb', diag=True)[0]

# No 2x2 can be all one thing
cons += all_2x2(lambda *a: And(Or(*[at(shaded, i) for i in a]), Or(*[Not(at(shaded, i)) for i in a])))

# Every non-first cell in a region must have the same shading as the first
cons += [at(shaded, i[0]) == at(shaded, j) for i in regions for j in i[1:]]

# Cells with symbols cannot be shaded
cons += [Not(at(shaded, i)) for i in inds() if at(g, i) != None]

# Start and goal must match
cons += [eq(start, tstart), eq(goal, tgoal)]

# Points on the path can't be shaded
cons += [Implies(some_edge(edge_vars, i), Not(at(shaded, i))) for i in inds()]

# Points with circles are on the path
cons += [some_edge(edge_vars, i) for i in inds() if at(g, i) == 'o']

# Points with triangles are not on the path
cons += [Not(some_edge(edge_vars, i)) for i in inds() if at(g, i) == 't']

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
