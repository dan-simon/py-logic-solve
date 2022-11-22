from z3 import Int, Bool, And, Or, If, Not, AtLeast, BoolRef, ArithRef, Solver, is_true, Implies, PbEq, Distinct
#  This doesn't work great if you want to solve nested puzzles, but otherwise it's good.

grid = None
height = None
width = None

# Initializes problem global data so functions from this file can use it
def set_problem(g):
    global grid
    global height
    global width
    grid = g
    height = len(g)
    width = len(g[0])

generator_type = type(i for i in range(10))

# z3 constraint: exactly one item in X is true.
def ExactlyOne(*a):
    a = list(a)
    if len(a) == 1 and type(a[0]) in (list, tuple, generator_type):
        return ExactlyOne(*a[0])
    return PbEq([(i, 1) for i in a], 1)

# Max for z3 variables
def Max(x, y):
    return If(x > y, x, y)

# Min for z3 variables
def Min(x, y):
    return If(x < y, x, y)

# Convert arrow to direction tuple
def to_dir(x, num=False):
    return '^>v<'.index(x) if num else orth_dir['^>v<'.index(x)]

# Get list of positions in the puzzle as tuples (the standard form of positions used by this library).
def inds(flat=True):
    if flat:
        return [(i, j) for i in range(height) for j in range(width)]
    else:
        return [[(i, j) for j in range(width)] for i in range(height)]

# Get the grid position opposite a given position (under 180-degree rotation).
def sym_op(x):
    return (height - x[0] - 1, width - x[1] - 1)

def column(x):
    if type(x) == tuple:
        return column(x[1])
    return [(i, x) for i in range(height)]

def row(x):
    if type(x) == tuple:
        return row(x[0])
    return [(x, j) for j in range(width)]

def rows():
    return [row(i) for i in range(height)]

def columns():
    return [column(i) for i in range(width)]

# Utility function to e.g. read a row or column from a given cell outside the grid.
def row_or_column(start, pos=None):
    if pos == None:
        pos = only([i for (i, j) in zip(start, (height, width)) if 0 <= i < j])
    opts = [start[0] < 0, start[1] >= width, start[0] >= height, start[1] < 0]
    d = opts.index(True) if True in opts else orth_dir.index(start)
    return (rows() if d % 2 else columns())[pos][::(-1 if d in (1, 2) else 1)]

# Get all edges (as 2-tuples of positions)
def edges(diag=False):
    return [(i, j) for i in inds() for j in neighbors(i, diag)]

# Get all edges with a given cell
def edges_around(x, diag=False):
    return [(x, j) for j in neighbors(x, diag)]

def at(x, i):
    return x[i[0]][i[1]]

def only(x):
    if type(x) in (list, tuple):
        x = set(x)
    assert len(x) == 1
    return list(x)[0]

# Some generally useful python list fuctions
def windows(l, n):
    if type(l) not in (list, tuple, str):
        l = list(l)
    return [l[i:i+n] for i in range(len(l) - n + 1)]

def sections(l, n):
    if type(l) not in (list, tuple, str):
        l = list(l)
    return [l[i:i+n] for i in range(0, len(l), n)]

# Get points in a straight line from a to b (only guaranteed to work for orthagonals and diagonals)
def basic_line_path(a, b):
    diffs = {abs(j - i) for (i, j) in zip(a, b)}
    assert len(diffs - {0}) <= 1
    m = max(diffs)
    return [tuple(round((i * (m - k) + j * k) / m) for (i, j) in zip(a, b)) for k in range(m + 1)]

# Draw a path with multiple points (more than two).
def line_path(*x):
    return [j for (ind, i) in enumerate(windows(x, 2)) for j in basic_line_path(*i)[ind > 0:]]

orth_dir = ((-1, 0), (0, 1), (1, 0), (0, -1))

diag_dir = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))

# Sme basic tuple manipulation as vectors
def plus(x, d):
    return (x[0] + d[0], x[1] + d[1])

def minus(x, d):
    return (x[0] - d[0], x[1] - d[1])

def times(x, y):
    if type(y) == int or type(y) == float:
        return times(y, x)
    return (x * y[0], x * y[1])

# z3 equality (for constraints); z3 obviously can't override "=="
# to use "And" rather than "and" on python lists.
def eq(a, b):
    if type(a) == dict:
        assert type(b) == dict and set(a.keys()) == set(b.keys())
        return And(*(eq(a[i], b[i]) for i in a))
    elif type(a) in (list, tuple):
        assert len(a) == len(b)
        return And(*(eq(i, j) for (i, j) in zip(a, b)))
    else:
        return a == b

# Take a z3 model and a collection of variables and reads the values of all the variables.
def read_model(m, x):
    if type(x) == dict:
        return {i: read_model(m, x[i]) for i in x}
    elif type(x) in (list, tuple):
        return type(x)(read_model(m, i) for i in x)
    else:
        # Note this still returns z3 values, not literals. This is relevant
        # if e.g. you're using a z3 bool in a python if; it'll throw an error.
        # More importantly, z3 possibly sometimes secretly mutates these,
        # causing code that assumes otherwise to throw an error (but maybe it doesn't).
        return m[x]

# Does the same as the above read_model, except it actually converts
# the values to python values, not z3 values.
def read_model_raw(m, x):
    if type(x) == dict:
        return {i: read_model_raw(m, x[i]) for i in x}
    elif type(x) in (list, tuple):
        return type(x)(read_model_raw(m, i) for i in x)
    elif type(x) == BoolRef:
        return is_true(m[x])
    elif type(x) == ArithRef:
        return m[x].as_long()
    else:
        raise Exception('Mysterious type passed into read_model_raw')

def neighbors(x, diag=False):
    r = [plus(x, d) for d in (diag_dir if diag else orth_dir)]
    return [i for i in r if in_bounds(i)]

def in_bounds(x):
    return 0 <= x[0] < height and 0 <= x[1] < width

# Unlike the above in_bounds, this returns a z3 constraint.
def InBounds(x):
    return And(0 <= x[0], x[0] < height, 0 <= x[1], x[1] < width)

def is_perimeter(x):
    return 0 == x[0] or height - 1 == x[0] or 0 == x[1] or width - 1 == x[1]

# This is a display function to show paths,
# given that they're represented at each cell by four values saying in which directions paths go.
def show_path(x, blank=' '):
    v = 8 * x[0] + 4 * x[1] + 2 * x[2] + x[3]
    return (blank + '╴╷┐╶─┌┬╵┘│┤└┴├┼')[v]

# And this shows the full path given an edge-to-bool dictionary
def show_full_path(edges, blank=' '):
    return '\n'.join(''.join(show_path([edges[(j, plus(j, k))] if in_bounds(plus(j, k)) else False for k in orth_dir], blank)
    for j in i) for i in inds(flat=False))

# Get an array of z3 variables. Useful for giving a number for each cell, for example.
def construct_vars(f, prefix, shape, so_far=()):
    if type(shape) == int:
        return construct_vars(f, prefix, (shape,), so_far)
    elif not shape:
        return f(prefix + '-'.join(str(i) for i in so_far))
    else:
        return [construct_vars(f, prefix, shape[1:], so_far + (i,)) for i in range(shape[0])]

# Same as above, except one z3 variable per edge.
def construct_edge_vars(f, prefix, edges):
    return {(i, j): f(prefix + 'e' + '-' + '-'.join(str(k) for k in i + j)) for (i, j) in edges}

# Some more python utilities
def shape(x):
    if type(x) in (list, tuple):
        return (len(x),) + shape(x[1])
    else:
        return ()

def flatten(x, depth=float('inf')):
    if depth > 0 and type(x) in (list, tuple):
        return [j for i in x for j in flatten(i, depth - 1)]
    else:
        return [x]

def deep_map(f, x, depth=float('inf')):
    if depth > 0 and type(x) in (list, tuple, dict):
        if type(x) == dict:
            return {i: deep_map(f, x[i], depth - 1) for i in x}
        return type(x)(deep_map(f, i, depth - 1) for i in x)
    else:
        return f(x)

# Integer parsing (for parsing puzzle data)
def parse_int(x, exc={}):
    if type(exc) == str:
        exc = {i: -1 for i in exc}
    return exc[x] if x in exc else (ord(x.upper()) - ord('A') + 10 if 'A' <= x.upper() <= 'Z' else (int(x) if x != '.' else None))

# Integet writing (for outputting puzzle solutions)
def write_int(x):
    return '?' if x >= 36 else (chr(ord('A') + x - 10) if x >= 10 else str(x))

# Turn a string into a grid.
def to_grid(x, section_size=1):
    return [sections(i.strip(), section_size) for i in x.strip().split('\n')]

# Take a string-format grid with different letters in each cell,
# creates a region of cells (list of positions) with each letter.
# Doesn't care about connectivity; two cells with the same letter
# will always be in the same region.
def parse_regions(x, periods=False, grid=True):
    assert periods or ('.' not in x)
    t = to_grid(x)
    a = [[(i, j) for i in range(len(t)) for j in range(len(t[i]))
    if t[i][j] == c] for c in set(''.join(''.join(i) for i in t)) - {'.'}]
    b = [[(i, j)] for i in range(len(t)) for j in range(len(t[i])) if t[i][j] == '.'] if periods else []
    return (sorted(a + b), t) if grid else sorted(a + b)

# Given a string-format grid with integer clues and a list of regions,
# return a list of (region index, clue value) pairs. Clues are expected to be
# in the first cell of each region (in top-bottom, left-right order).
def parse_clues(c, r):
    t = to_grid(c)
    firsts = [i[0] for i in r]
    assert all((i, j) in firsts for i in range(len(t)) for j in range(len(t[i])) if t[i][j] != '.')
    r = [(ind, parse_int(t[i][j])) for (ind, (i, j)) in enumerate(firsts)]
    return [i for i in r if i[1] != None]

# Parse a string-format grid of integers (using . for cells without integers).
def parse_int_grid(g, exc={}):
    return deep_map(lambda x: parse_int(x, exc), to_grid(g), depth=2)

# Given a list of regions, make a {cell: index of region with cell} table.
def get_rtable(r):
    return {j: ind for (ind, i) in enumerate(r) for j in i}

# Some rotation + translation stuff for genres like LITS where you need to consider
# all positionings of something in a region.
def rot_loc(x, d='right'):
    return {'left': (-x[1], x[0]), 'right': (x[1], -x[0])}[d]

def rot_locs(locs, d='right'):
    return normalize_locs([rot_loc(i, d) for i in locs])

def refl_locs(locs):
    return normalize_locs([(-i[0], i[1]) for i in locs])

def normalize_locs(x):
    return tuple(sorted(minus(i, min(x)) for i in x))

def positioning(locs, refl=True):
    pos = [locs, rot_locs(locs), rot_locs(rot_locs(locs)),
    rot_locs(rot_locs(rot_locs(locs)))]
    if refl:
        pos += [refl_locs(i) for i in pos]
    r = [tuple(plus(j, k) for k in i) for i in pos for j in inds()]
    return sorted(set(i for i in r if all(in_bounds(j) for j in i)))

# A special case of construct_vars, typically used when certain cells are shaded.
def shaded_vars(s):
    return construct_vars(Bool, s, (height, width))

# checks that regions are connected.
# rv: table of regions (generally for genres like fillomino,
# where this is computed by z3).
# included: is this cell in a region at all, or is it somehow not in any regions?
# base: is this cell a "region base"? Generally you want to somehow make sure each region
# has only one base.
# cs: string to name z3 variables using.
# diag: are diagonal connections allowed?
# rect: must regions be rectangles? (like in shikaku)
def connected(rv, included, base, cs, **kwargs):
    diag = bool(kwargs.get('diag'))
    rect = bool(kwargs.get('rect'))
    dist = construct_vars(Int, cs, (height, width))
    cons = [Implies(included(i), Or(base(i), *[And(
    included(j), eq(at(rv, i), at(rv, j)), at(dist, i) < at(dist, j)
    ) for j in neighbors(i, diag)])) for i in inds()]
    if rect:
        cons += rectangular_regions(rv, included)
    return cons, dist

# Do two z3 region grids agree about which regions everything is in, except for naming of course?
def same_regions(r1, r2):
    return [eq(at(r1, i), at(r1, j)) == eq(at(r2, i), at(r2, j)) for (i, j) in edges()]

# Get sizes of regions (defined by rv).
# included, base: as in connected above (except that base might care about region value)
# nonbase: is this cell not a base cell? not always the negation of base
# bc you can sometimes do tricks, like require the base to be minimal in the region in some way
# and thus require nonbase cells to be "greater" than the base.
# cs: as above
# same_size: does the size have to be the same for all cells in the same region?
# This should be true generally. Though sometimes (read: in fillomino) it's wise to
# number non-adjacent regions the same, in the specific case of fillomino they have the same size.
# However, this follows from other constraints there so is redundant and slows things down.
# This function is generally slower than other options. I've sped up islands and nurikabe
# by replacing it by a sum.
def get_sizes(included, base, nonbase, cs, same_size=True):
    rv = construct_vars(Int, cs + 'r', (height, width))
    dist = construct_vars(Int, cs + 'd', (height, width))
    edge_use = construct_edge_vars(Bool, cs + 'e', edges())
    edge_size = construct_edge_vars(Int, cs + 'es', edges())
    size = construct_vars(Int, cs + 's', (height, width))
    cons = [at(dist, i) >= 0 for i in inds()]
    cons += [Implies(included(i, at(rv, i)), If(at(dist, i) == 0, base(i, at(rv, i)),
    And(nonbase(i, at(rv, i)), ExactlyOne(*[edge_use[(i, j)] for j in neighbors(i)]))))
    for i in inds()]
    cons += [Implies(edge_use[(i, j)], And(included(i, at(rv, i)), included(j, at(rv, j)),
    at(dist, i) == at(dist, j) + 1, eq(at(rv, i), at(rv, j))))
    for (i, j) in edges()]
    cons += [edge_size[(i, j)] == If(Or(edge_use[(i, j)], edge_use[(j, i)]),
    1 + sum(edge_size[(j, k)] for k in neighbors(j) if i != k), 0) for (i, j) in edges()]
    cons += [edge_size[(i, j)] >= 0 for (i, j) in edges()]
    cons += [at(size, i) == 1 + sum(edge_size[(i, j)] for j in neighbors(i)) for i in inds()]
    # The i < j condition here avoids duplication. This condition speeds stuff up quite a bit, except when it doesn't.
    if same_size:
        cons += [Implies(eq(at(rv, i), at(rv, j)), eq(at(size, i), at(size, j))) for i in inds() for j in neighbors(i) if i < j]
    return cons, rv, dist, edge_use, edge_size, size

# Define a path.
# circ: does the path make a loop (True), or have a potentially different start and end (False)
# cs: as above
# return_dist: do we return distances along the path?
def path(circ, cs, return_dist=False):
    edge_vars = construct_edge_vars(Bool, cs, edges())
    cons = []
    if circ:
        root = Int(cs + 'rx'), Int(cs + 'ry')
        cons += [InBounds(root)]
    else:
        start = Int(cs + 'sx'), Int(cs + 'sy')
        end = Int(cs + 'ex'), Int(cs + 'ey')
        cons += [InBounds(start), InBounds(end)]
    r = root if circ else start
    if circ:
        cons += [Or(PbEq([(edge_vars[(i, j)], 1) for j in neighbors(i)], 0), PbEq([(edge_vars[(i, j)], 1) for j in neighbors(i)], 2)) for i in inds()]
    else:
        cons += [Or(PbEq([(edge_vars[(i, j)], 1) for j in neighbors(i)], 0), If(Or(eq(i, start), eq(i, end)),
        PbEq([(edge_vars[(i, j)], 1) for j in neighbors(i)], 1), PbEq([(edge_vars[(i, j)], 1) for j in neighbors(i)], 2))) for i in inds()]
    dist = construct_vars(Int, cs + 'd', (height, width))
    cons += [Implies(some_edge(edge_vars, i),
    Or(eq(i, r), *[And(edge_vars[(i, j)], at(dist, j) < at(dist, i)) for j in neighbors(i)])) for i in inds()]
    cons += symmetric_edges(edge_vars)
    if circ:
        return (cons, edge_vars, root) + (dist,) * return_dist
    else:
        return (cons, edge_vars, start, end) + (dist,) * return_dist

# Does some edge around x in this edge-variable table e have a True variable?
def some_edge(e, x, diag=False):
    return Or(*[e[(x, y)] for y in neighbors(x, diag)])

# Propagate stuff in various directions. Useful for e.g. Cave, Skyscraper, Yajilin.
def look(f, tf, cs):
    findings = construct_vars(tf, cs, (4, height, width))
    cons = [at(findings[di], i) == f(i, d, False, plus(i, d), at(findings[di], plus(i, d)))
    if in_bounds(plus(i, d)) else (at(findings[di], i) == f(i, d, True, i, 0))
    for i in inds() for (di, d) in enumerate(orth_dir)]
    return cons, findings

# List of constraints about whether all neighbor pairs i and j have a certain property f
# (should be symmetric, because we only include i < j).
def all_neighbors(f, diag=False):
    return [f(i, j) for i in inds() for j in neighbors(i, diag) if i < j]

# Similar to above, list of constraints about whether all 2x2 groups of 4 cells have a certain property f.
def all_2x2(f):
    near = lambda x: [plus(x, (i, j)) for i in (0, 1) for j in (0, 1)]
    return [f(*near(i)) for i in inds() if all(in_bounds(j) for j in near(i))]

# Checks whether a region is rectangular.
def rectangular_regions(rv, included=lambda _: True):
    return all_2x2(lambda *a: And(
    Implies(And(included(a[0]), included(a[3]), eq(at(rv, a[0]), at(rv, a[3]))), And(eq(at(rv, a[0]), at(rv, a[1])), eq(at(rv, a[0]), at(rv, a[2])))),
    Implies(And(included(a[1]), included(a[2]), eq(at(rv, a[1]), at(rv, a[2]))), And(eq(at(rv, a[1]), at(rv, a[0])), eq(at(rv, a[1]), at(rv, a[3]))))))

# Checks whether each edge is the same as its reverse in some edge table. Useful for e.g.
# undirected loop genres
def symmetric_edges(x):
    return [eq(x[i], x[i[::-1]]) for i in edges()]

