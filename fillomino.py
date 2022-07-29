from z3 import Solver
from lib import set_problem, parse_int_grid, at, get_sizes, inds, same_regions, write_int
import time

g = parse_int_grid('''
341..2...2
.....3.1.4
.422.3.4.1
.......1..
122.41....
....44.332
..1.......
2.3.3.141.
1.2.3.....
3...1..212
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Divide all cells of grid into regions. same_size=False speeds things up slightly due to those constraints not helping much.
c, rv, _, edge_uses, edge_sizes, sizes = get_sizes((lambda _, _2: True), (lambda i, x: x == i[0] * width + i[1]), (lambda i, x: x < i[0] * width + i[1]), 's', same_size=False)
cons += c

# This is the trick: region number = sizes. So multiple non-adjacent regions can have the same region number.
# We could still do same_size=True above though, but this tells us more. 
cons += same_regions(sizes, rv)

# Clues must be accurate.
cons += [at(sizes, i) == at(g, i) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join(write_int(m[j].as_long()) for j in i) for i in sizes))
