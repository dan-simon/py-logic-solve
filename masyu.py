from z3 import Int, And, If, Or, Solver, is_true
from lib import set_problem, deep_map, to_grid, at, inds, look, path, read_model, show_full_path, some_edge
import time

def parse(g):
    return deep_map(lambda x: x if x != '.' else None, to_grid(g), depth=2)

g = parse('''
...W...W..
...W......
B....B.W..
...B.B....
..........
..W....B.W
...W.W....
.W........
WW.W.WW..B
..........
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Create a path
c, link, _ = path(True, 'l')
cons += c

# Find length of line segment visible from a point in each direction.
c, vis = look((lambda p, d, edge, n, v: 0 if edge else If(link[(p, n)], v + 1, 0)), Int, 'v')
cons += c

# Add black cell constraints (must have path, must have either horizontal or vertical segment (not both),
# must not have any segment of length 1)
cons += [And(some_edge(link, i), (at(vis[0], i) == 0) != (at(vis[2], i) == 0),
And(*[at(vis[j], i) != 1 for j in range(4)])) for i in inds() if at(g, i) == 'B']

# Add white cell constraints (must have path, must have either both horizontal or vertical segment or neither of them,
# must have some segment of length 1)
cons += [And(some_edge(link, i), (at(vis[0], i) == 0) == (at(vis[2], i) == 0),
Or(*[at(vis[j], i) == 1 for j in range(4)])) for i in inds() if at(g, i) == 'W']

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print(show_full_path(deep_map(is_true, read_model(m, link))))
