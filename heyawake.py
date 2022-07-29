from z3 import Int, And, If, Not, Or, PbEq, Solver, is_true
from lib import set_problem, parse_regions, parse_clues, all_neighbors, at, connected, \
eq, get_rtable, inds, look, shaded_vars
import time

regions, g = parse_regions('''
AAAABBBBCCCDDDDEEEFFGGHH
AAAAIIJJCCCDDDDEEEFFGGHH
KKKKIIJJCCCDDDDEEELLLMHH
KKKKNNOOCCCPPQQQRRLLLMSS
KKKKNNOOTTTPPQQQRRUUUMSS
KKKKNNOOTTTVVVVVRRUUUMSS
WWXYYYYYZZaaabbbcccddeee
WWXYYYYYZZaaabbbcccddeee
ffXYYYYYZZaaabbbgggddeee
ffXhhhiiZZaaabbbgggddjjk
llXhhhiiZZaaabbbgggmmjjk
llXhhhiiZZnnnnoopppmmjjk
qqqrrsssZZnnnnoopppttjjk
qqqrrsssZZnnnnoopppttjju
''')

clues = parse_clues('''
3...2...5..3...3..2.....
......2.................
5.................1..2..
.............2........2.
........2.........3.....
........................
2.36......6.....3..3.3..
........................
................4.......
...1..2..............1.2
...................1....
..............1.2.......
...2.2.............2....
........................
''', regions)

rtable = get_rtable(regions)

same_region = lambda i, j: rtable[i] == rtable[j]

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

# root of the unshaded cells (which must be connected)
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

# pairs of shaded cells cannot be adjacent
cons += all_neighbors(lambda x, y: Or(Not(at(shaded, x)), Not(at(shaded, y))))

# count regions visible along each line
c, vis = look((lambda pos, d, edge, n, v: If(at(shaded, pos), 0, If(And(same_region(pos, n) and not edge, Not(at(shaded, n))), v, v + 1))), Int, 'v')
cons += c

# There are always 1 or 2 regions visible in a line from an unshaded cell, and 0 in a line from a shaded cell
cons += [And(at(j, i) >= 0, at(j, i) < 3) for i in inds() for j in vis]

# Satisfy given clues
cons += [PbEq([(at(shaded, j), 1) for j in regions[i]], v) for (i, v) in clues]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))

