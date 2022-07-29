from z3 import Int, And, Not, Or, Solver, is_true
from lib import set_problem, deep_map, to_grid, all_2x2, at, connected, eq, inds, shaded_vars
import time

def parse(g):
    return deep_map(lambda x: x if x != '.' else None, to_grid(g), depth=2)

g = parse('''
.........
.B.W.W.W.
..W.B.W..
.B.W.W.B.
..W.W.W..
.B.W.B.W.
..W.B.W..
.B.W.B.W.
.........
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

shaded = shaded_vars('s')

# Ensure both white and black cells are connected to some root; make this root a clue if possible
def first_index(x, otherwise):
    opts = [i for i in inds() if at(g, i) == x]
    return opts[0] if opts else otherwise

wroot = first_index('W', (Int('w1'), Int('w2')))
broot = first_index('B', (Int('b1'), Int('b2')))

cons += connected(shaded, (lambda x: Not(at(shaded, x))), (lambda x: eq(wroot, x)), 'w')[0]
cons += connected(shaded, (lambda x: at(shaded, x)), (lambda x: eq(broot, x)), 'b')[0]

# Black-circle clues are shaded, and white-circle clues aren't
cons += [at(shaded, i) == (at(g, i) == 'B') for i in inds() if at(g, i) != None]

# No 2x2 is all one color
cons += all_2x2(lambda *a: And(Or(*[at(shaded, i) for i in a]), Or(*[Not(at(shaded, i)) for i in a])))

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
