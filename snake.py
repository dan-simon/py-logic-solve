from z3 import And, If, Implies, Not, Or, Solver, is_true
from lib import set_problem, deep_map, to_grid, all_2x2, at, columns, edges, eq, \
inds, path, rows, shaded_vars, some_edge
import time

def parse(g):
    return deep_map(lambda x: int(x) if '0' <= x <= '9' else (x if x != '.' else None), to_grid(g), depth=2)

g = parse('''
X6.2.1.6
........
........
..W.....
....B...
......W.
4.......
........
''')

# Divide the grid into clues giving number of shaded spaces on each row,
# clues giving number of shaded spaces on each column, and the grid itself.
row_clues = [i[0] for i in g[1:]]

column_clues = g[0][1:]

g = [i[1:] for i in g[1:]]

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Set up a path
c, edge_vars, end1, end2 = path(False, 'l')
cons += c

# Set up a shading
shaded = shaded_vars('s')

# A cell is part of the path if and only if it's shaded
cons += [eq(some_edge(edge_vars, i), at(shaded, i)) for i in inds()]

# Any two orthogonally adjacent cells in the path must be directly connected
cons += [Implies(And(at(shaded, i), at(shaded, j)), edge_vars[(i, j)]) for (i, j) in edges()]

# Any two diagonally adjacent cells in the path must both connect to one of the cells
# they're both orthogonally adjacent to
diag_cond = lambda t1, t2: Implies(And(*[at(shaded, i) for i in t1]), Or(*[And(*[edge_vars[(i, j)] for i in t1]) for j in t2]))
cons += all_2x2(lambda a, b, c, d: And(diag_cond((a, d), (b, c)), diag_cond((b, c), (d, a))))

# A black-circle cell must be at an end of the path
cons += [And(at(shaded, i), Or(*[eq(i, end1), eq(i, end2)])) for i in inds() if at(g, i) == 'B']

# A white-circle cell must be in the path, but not at an end
cons += [And(at(shaded, i), Not(Or(*[eq(i, end1), eq(i, end2)]))) for i in inds() if at(g, i) == 'W']

# The row and column clues for number of shaded cells must be correct
cons += [sum(If(at(shaded, i), 1, 0) for i in r) == t for (r, t) in zip(rows(), row_clues) if t != None]
cons += [sum(If(at(shaded, i), 1, 0) for i in r) == t for (r, t) in zip(columns(), column_clues) if t != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print('\n'.join(''.join('.#'[is_true(m[j])] for j in i) for i in shaded))
