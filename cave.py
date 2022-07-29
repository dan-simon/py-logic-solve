from z3 import Int, And, If, Implies, Not, Solver, is_true
from lib import set_problem, parse_int_grid, all_2x2, at, connected, eq, inds, is_perimeter, look, shaded_vars
import time

g = parse_int_grid('''
...3.6....
.3..4.....
5.4..3...4
.4......3.
.........4
4.........
.3......3.
3...4..5.5
.....4..5.
....5.5...
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

# root of the unshaded cells (which must be connected)
root = Int('r1'), Int('r2')

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(root, x)), 'uc')[0]

# all shaded cells must be connected to the perimeter
cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: is_perimeter(x)), 'c')[0]

# no 2x2 checkerboards
cons += all_2x2(lambda a, b, c, d: Implies(And(at(shaded, a) == at(shaded, d), at(shaded, b) == at(shaded, c)),
at(shaded, a) == at(shaded, b)))

# how many other cells are visible in a certain direction
c, vis = look((lambda pos, d, edge, n, v: 0 if edge else If(at(shaded, n), 0, v + 1)), Int, 'v')
cons += c

# add the constraints from clues
cons += [sum(at(it, i) for it in vis) == at(g, i) - 1 for i in inds() if at(g, i) != None]

# add the constraint that clues cannot be shaded
cons += [Not(at(shaded, i)) for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
