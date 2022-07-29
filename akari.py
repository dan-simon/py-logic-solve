from z3 import Int, And, If, Not, Or, PbEq, Solver, is_true
from lib import set_problem, parse_int_grid, at, inds, look, neighbors, shaded_vars
import time

g = parse_int_grid('''
X....1......1....1
...1....XX....1...
......1....1......
.1..............X.
....1...11...X....
....1...11...1....
.X..............1.
......X....X......
...X....11....X...
1....1......1....1
''', exc={'X': -1})

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

lights = shaded_vars('l')

# lights can only go on cells with no clues
cons += [Not(at(lights, i)) for i in inds() if at(g, i) != None]

# Look for a light in given direction (indeed, count lights before black cell)
c, vis = look((lambda pos, d, edge, n, v: False if at(g, pos) != None else If(edge, 0, v) + If(at(lights, pos), 1, 0)), Int, 'v')
cons += c

# add the constraints that every cell is either unlit in a direction or once-lit, and that every cell must be lit in at least one direction
cons += [And(And(*[Or(at(lit, i) == 0, at(lit, i) == 1) for lit in vis]), Or(*[at(lit, i) == 1 for lit in vis])) for i in inds() if at(g, i) == None]

# add the constraints that the number of lights around each clue is as indicated
cons += [PbEq([(at(lights, j), 1) for j in neighbors(i)], at(g, i)) for i in inds() if at(g, i) != None and at(g, i) >= 0]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('#' if j != None else '.*'[is_true(m[k])] for (j, k) in zip(*i)) for i in zip(g, lights)))
