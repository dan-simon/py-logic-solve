from z3 import And, Not, PbEq, Solver, is_true
from lib import set_problem, parse_regions, all_neighbors, at, columns, rows, shaded_vars
import time

regions, g = parse_regions('''
AAAAABBBB
AAAAACBBB
AAACCCCBB
DDDDCCCBB
DDDDCEEEE
DFFFFGEEE
HHFFFGGEI
HHFGGGGII
HHHGGGIII
''')

star_count = 2

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Set up stars (use shaded_vars even though stars aren't usually shaded because it works the same way)
stars = shaded_vars('s')

# Every row has the required number of stars
cons += [PbEq([(at(stars, j), 1) for j in i], star_count) for i in rows()]

# Every column has the required number of stars
cons += [PbEq([(at(stars, j), 1) for j in i], star_count) for i in columns()]

# Every region has the required number of stars
cons += [PbEq([(at(stars, j), 1) for j in i], star_count) for i in regions]

# No pair of neighbors can both have stars
cons += all_neighbors((lambda x, y: Not(And(at(stars, x), at(stars, y)))), diag=True)

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.*'[is_true(m[j])] for j in i) for i in stars))
