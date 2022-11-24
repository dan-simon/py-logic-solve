from z3 import Int, And, Implies, Or, Solver
from lib import set_problem, deep_map, parse_int, to_grid, at, connected, \
construct_vars, inds, write_int
import time

def parse_clue(x):
    r = [parse_int(i, {'?': -1, '.': None}) for i in x]
    r = [i for i in r if i != None]
    return r or None

def parse(g, n):
    return deep_map(parse_clue, to_grid(g, section_size=n), depth=2)

g = parse('''
...........................
...13....123...............
...........................
............123............
......123..................
...........................
...........................
..................123......
...........................
''', 3)

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

clues = [i for i in inds() if at(g, i) != None]

nums = [[Int('n' + str(ind) + '-' + str(ind2)) for (ind2, j) in enumerate(at(g, i))] for (ind, i) in enumerate(clues)]

# Given values (which are most of them)
cons += [j1 == j2 for (i1, i2) in zip(clues, nums) for (j1, j2) in zip(at(g, i1), i2) if j1 != -1]

# Distinct-value condition
cons += [j1 != j2 for i in nums for (ind1, j1) in enumerate(i) for j2 in i[ind1 + 1:]]

cons += [And(0 < j, j <= max(width, height)) for i in nums for j in i]

# Regions (one per clue)
rs = construct_vars(Int, 'r', (height, width))

# Each region must all connect to its clue
cons += connected(rs, (lambda _: True), (lambda x: at(rs, x) == clues.index(x) if x in clues else False), 'c')[0]

# There are no regions with a number higher than the number of clues
cons += [And(0 <= at(rs, i), at(rs, i) < len(clues)) for i in inds()]

# Clues must be part of their regions
cons += [at(rs, i) == ind for (ind, i) in enumerate(clues)]

# Form all line segments in the grid
def get_horiz_lines(h, w):
    return [([(i, k) for k in range(j1, j2)], [(i, j1 - 1)] * (j1 > 0) + [(i, j2)] * (j2 < w))
    for i in range(h) for j1 in range(w) for j2 in range(j1 + 1, w + 1)]

lines = get_horiz_lines(height, width) + [tuple([k[::-1] for k in j] for j in i) for i in get_horiz_lines(width, height)]

# Separate out line segments by length
line_length = [[] for _ in range(max(height, width) + 1)]
for i in lines:
    line_length[len(i[0])].append(i)

# A line segement of given length appears in a region if and only if it's a clue number for that region
# (We also have to check that the line segment doesn't extend longer, hence our inclusion of extra cells on either side.)
cons += [Or(*[j == v for j in i]) == Or(*[And(*([at(rs, j) == ind for j in p[0]] +
[at(rs, j) != ind for j in p[1]])) for p in line_length[v]])
for (ind, i) in enumerate(nums) for v in range(1, max(height, width) + 1)]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join(write_int(m[j].as_long()) for j in i) for i in rs))
