from z3 import Int, And, If, Not, Or, Solver, is_true
from lib import set_problem, parse_regions, parse_clues, at, connected, construct_vars, \
edges, eq, get_rtable, inds, shaded_vars
import time

regions, g = parse_regions('''
AABBCDDDEEFF
AABBGGGGEEFF
HHBBGGGGEEII
HHJJJKKKLLII
MMMNNKKKOOII
MMMNNPPPOOQQ
MMMNNPPPRRQQ
SSTTUUUURRVV
SSTTWWWXXYVV
SSZZWWWXXYVV
aabbWWWXXYcc
aabbddeeeecc
''')

clues = parse_clues('''
4.........3.
............
............
............
............
............
............
............
............
............
1.........2.
............
''', regions)

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

rtable = get_rtable(regions)

cons = []

shaded = shaded_vars('s')

# Create a root for shaded cells and a size for each group of shaded cells
# root = construct_vars(Int, 'r', (len(regions),))
root = construct_vars(Int, 'r', (len(regions), 2))

# Straightforwardly compute number of black squares in each region
sizes = [sum(If(at(shaded, j), 1, 0) for j in i) for i in regions]

rv = [[rtable[j] for j in i] for i in inds(flat=False)]

# Require black squares in each region to be connected
cons += connected(rv, (lambda x: at(shaded, x)), (lambda x: eq(x, root[rtable[x]])), 'c')[0]

# require that each region has a shaded root
cons += [Or(*[And(at(shaded, j), eq(root[i], j)) for j in regions[i]]) for i in range(len(regions))]

# require that no adjacent cells in different regions are both shaded
cons += [Or(Not(at(shaded, i)), Not(at(shaded, j))) for (i, j) in edges() if i < j and rtable[i] != rtable[j]]

# find adjacent regions
ar = sorted({(rtable[i], rtable[j]) for (i, j) in edges() if rtable[i] < rtable[j]})

# require adjacent regions to have different shaded-cell-sizes
cons += [Not(eq(sizes[i], sizes[j])) for (i, j) in ar]

# require every region has a size > 0 and <= its number of cells (this seems to give a 10%-20% speedup)
cons += [And(sizes[i] > 0, sizes[i] <= len(regions[i])) for i in range(len(regions))]

# require that regions with clued size have that size
cons += [sizes[i] == j for (i, j) in clues]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
