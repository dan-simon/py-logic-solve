from z3 import Int, If, Not, Or, Solver, is_true
from lib import set_problem, deep_map, parse_int, to_dir, to_grid, \
all_neighbors, at, inds, look, path, read_model, shaded_vars, show_full_path, some_edge
import time

def parse(g):
    return deep_map(lambda x: 1 if x == '##' else ((parse_int(x[0]), to_dir(x[1], num=True))
    if x != '..' else None), to_grid(g, section_size=2), depth=2)

g = parse('''
................................................................................
................................5>##............................................
..........................4<##0^##5>##4v........................................
......................1^3<......................................................
..................5v4v............................######........................
................##..............................####..####......................
..............##................................##..4<..2>......................
..............##..................................######........................
................####6>##........................................................
..................8>##..........................................................
..............##5>..............................................................
............##..................................................................
..........5^....................................................................
........4>....................##0<......................................######..
........9>..................####..##........4^3^4^4>................####....##..
........2<........3v##......4<..####........##......####..........##........##..
..........########............####..........##..........2v......##..........##..
............####..............................4v..........2v..##............##..
......####4v##................................9<............7^##................
....9v......##................................2>..............##..........######
4v..........3>..................................##......................####....
..##........A>..................................##........##......##..##........
....9^##....##....................................##3>......5v..##..............
........2^..##4>..............................####......0>........####..........
..............7>##..........................##............3>....................
..............########6^..........##2v2v####..........4<8^....##..##......######
............0<..........##3^5>8^##........##..................##....##......##..
............##..##......................2<....................................##
..........##......##..........0v####..##..............3>........................
..........##......##............####..##A^########3^3<3^..........3v............
..........##....##..............####................4>............##D^..........
............##..##................##................9<..........######3v........
................##..................................2>..........##..##....5<....
..............##......................................##......####....##....6^5^
..............0<7>##........................##........##....####........##......
................####................##....######......######..............####..
..................1<##............##..2>........####4<............##........##..
......................##########4<9^2>##............9^............##....A^####..
......................................##........##..2>..........####..##........
......................................##......####..............##........######
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

cons = []

# Create a loop
c, link, _ = path(True, 'l')
cons += c

# Create a shading
shaded = shaded_vars('s')

# Force the loop not to go through clues
cons += [Not(some_edge(link, i)) for i in inds() if at(g, i) != None]

# Clues cannot be shaded
cons += [Not(at(shaded, i)) for i in inds() if at(g, i) != None]

# Non-clues either have the loop going through them or are shaded, but never both
cons += [some_edge(link, i) != at(shaded, i) for i in inds() if at(g, i) == None]

# No two neighbors can be shaded
cons += all_neighbors(lambda x, y: Or(Not(at(shaded, x)), Not(at(shaded, y))))

# Count shaded cells in a direction
c, vis = look((lambda pos, d, edge, n, v: 0 if edge else v + If(at(shaded, n), 1, 0)), Int, 'v')
cons += c

# Check that the shaded cell counts match the clues
cons += [at(vis[at(g, i)[1]], i) == at(g, i)[0] for i in inds() if at(g, i) != None and at(g, i) != 1]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print(show_full_path(deep_map(is_true, read_model(m, link)), blank='#'))
