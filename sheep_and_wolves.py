from z3 import Bool, Int, And, Implies, Or, PbEq, Solver, is_true
from lib import set_problem, deep_map, to_grid, all_neighbors, at, connected, \
construct_vars, edges, inds, minus, orth_dir, plus, read_model, show_path
import time

# This is probably the messiest genre I've coded. The natural variables are these
# "long edge" that go along grid edges rather than between grid cells
# (starting and ending at either the perimeter or dots). Handling the fact
# that these long edges are different lengths and don't correspond straightforwardly
# to actual edges takes a lot of code.

def parse(g):
    return deep_map(lambda x: x if x != '.' else None, to_grid(g), depth=2)

def parse_dots(g):
    return deep_map(lambda x: {'O': True, '.': False}[x], to_grid(g), depth=2)

g = parse('''
S....S..S.
.WWSS.....
.......W..
.S.S..S...
.W..W..W.W
W....W..W.
W.S..WW...
....W.....
.S....S..W
W....W....
''')

dots = parse_dots('''
....O....
...O..O..
.O...O...
..O......
.O.O..OOO
.O....O..
.O..O....
O.......O
O.......O
''')

height = len(g)
width = len(g[0])
set_problem(g)
tm = time.time()

# We index grid cell intersections (not aligned with grid)
# by -1, -1 = very top-left corner. This function tells us if an intersection
# is inside the grid as opposed to on the edge.
def in_altered_bounds(x):
    return 0 <= x[0] < height - 1 and 0 <= x[1] < width - 1

# This function tells us if an intersection is inside the grid or on the edge,
# as opposed to off the grid entirely.
def in_expanded_bounds(x):
    return -1 <= x[0] < height and -1 <= x[1] < width

# This function takes an edge between two grid cells and gets the endpoints
# of the long edge (edge between two dots, one or both of which may instead
# be the grid perimeter, and aligned with cell intersections) that the edge
# corresponds to.
def get_long_edge(e):
    # We want our only options to be that the first cell is either directly above
    # or directly to the left of the second.
    low, high = sorted(e)
    # Get the coordinates of the intersection of the edge between these two cells
    # (how to do this depends on whether the first cell is above the second cell,
    # i.e. low[0] < high[0] and low[1] = high[1], or if not,
    # i.e. low[0] = high[0] and low[1] < high[1]).
    left = (low[0], low[1] - 1) if low[0] < high[0] else (low[0] - 1, low[1])
    right = low
    # Now extend the edge in both directions until it hits a dot or the edge.
    return extend(left, right)

# This function takes two adjacent grid intersections (provided via coordinates)
# and gets the long edge that the edge between them is part of.
# Note that the input is already grid intersections, not grid cells.
def extend(left, right):
    # Make sure the first is less than the second. This is so we can make sure
    # every long edge has this property and we don't have one long edge
    # that is the reverse of another (which could cause bugs).
    left, right = sorted((left, right))
    # Get the difference, subtract it from the left as much as needed for the left
    # to hit a dot or the edge, and add it to the right as much as needed for the right
    # to hit a dot or the edge.
    diff = minus(right, left)
    while in_altered_bounds(left) and not at(dots, left):
        left = minus(left, diff)
    while in_altered_bounds(right) and not at(dots, right):
        right = plus(right, diff)
    # Return the endpoints (which are now both either a dot or the edge).
    return left, right

# Get the long edges around a grid intersection (this is useful when it's a dot,
# since we know in that case exactly two of them must be used).
def around_dot(x):
    return [extend(x, plus(x, i)) for i in orth_dir]

# Check if both endpoints of a long edge are not on the edge of the grid.
def edge_internal(x):
    return all(in_altered_bounds(i) for i in x)

# Make a list of all dot locations.
def dot_list():
    return [i for i in inds() if in_altered_bounds(i) and at(dots, i)]

# Display a solution (given via edge variables).
# We can't use the standard loop display code because it's built
# for the case of length-one edges between grid cells.
def display(edge_vars):
    # Indices for grid intersections (including those on the perimeter).
    # The top-left corner is (-1, -1), while the bottom-right corner is (height - 1, width - 1)
    extended_inds = [[(u, v) for v in range(-1, width)] for u in range(-1, height)]
    # The key part of this is (in_altered_bounds(j) or in_altered_bounds(plus(j, k))) and
    # edge_vars[extend(j, plus(j, k))], which checks if at least one of j and j + k
    # is inside the grid and if the extended edge between them is used
    # (if both are on the edge of the grid, there is no extended edge between them
    # in the edge table, so checking for it will throw an error). This is the equivalent of
    # "is there an edge between two adjacent cells" in other genres' loop display functions.
    return '\n'.join(''.join(show_path([
    (in_altered_bounds(j) or in_altered_bounds(plus(j, k))) and
    edge_vars[extend(j, plus(j, k))] for k in orth_dir
    ], ' ') for j in i) for i in extended_inds)

cons = []

# Get a list of all long edges by finding the long edges corresponding to all edges.
long_edges = sorted({get_long_edge(i) for i in edges()})

# For each long edge, create both a boolean variable giving whether it's used or not,
# and an integer variable giving its distance to the perimeter of the puzzle, very vaguely
# (all we can say is that lower "distance" is closer).
edge_vars = {i: Bool('e' + str(ind)) for (ind, i) in enumerate(long_edges)}
edge_conn = {i: Int('c' + str(ind)) for (ind, i) in enumerate(long_edges)}

# Divide the cells both into regions (surrounded by edges),
# and also into two groups depending on if they're in a wolf area (True in sw_vars)
# or in a sheep area (False in sw_vars).
# Note: regions can be colored in a checkerboard pattern, so it's OK to use bool for them rather than int.
# In theory we could thius do display via shading regions, but since two adjacent regions might be the same
# with respect to having sheep or wolves, that would likely be confusing.
region_vars = construct_vars(Bool, 'r', (height, width))
sw_vars = construct_vars(Bool, 'sw', (height, width))

# Every dot must have two used long edges around it.
cons += [PbEq([(edge_vars[j], 1) for j in around_dot(i)], 2) for i in dot_list()]

# Every edge that does not touch the grid perimeter must have a neighbor that is "closer" to the grid perimeter.
cons += [Or(*[And(edge_vars[k], edge_conn[k] < edge_conn[i]) for j in i for k in around_dot(j) if k != i])
for i in long_edges if edge_internal(i)]

# Each region must be connected to either a sheep or a wolf (checks that it's not both will come later).
cons += connected(region_vars, (lambda _: True), (lambda x: at(g, x) != None), 'c')[0]

# Every two cells must have a used long edge between them if and only if they are not part of the same region.
# Unlike in border block, a region can't loop around to touch itself.
cons += all_neighbors(lambda i, j: edge_vars[get_long_edge((i, j))] == (at(region_vars, i) != at(region_vars, j)))

# If one of two cells is in a sheep area and the other is in a wolf area, there must be an edge between them.
# (And thus they must be in different regions.)
cons += all_neighbors(lambda i, j: Implies(at(sw_vars, i) != at(sw_vars, j), edge_vars[get_long_edge((i, j))]))

# All sheep and wolves must be in the proper type of area (sheep in sheep areas, wolves in wolf areas).
cons += [at(sw_vars, i) == {'S': False, 'W': True}[at(g, i)] for i in inds() if at(g, i) != None]

t0 = time.time()
print('constructed', t0 - tm)
s = Solver()
s.add(*cons)
print(s.check())
print('done', time.time() - t0)
m = s.model()
print(display(deep_map(is_true, read_model(m, edge_vars))))
