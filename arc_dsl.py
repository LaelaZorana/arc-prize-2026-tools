"""
ARC-AGI-2 Domain Specific Language
Primitive operations for program synthesis solver.
All functions return new grids and never mutate in place.
Grids are list[list[int]], integers 0-9 (0 = background by default).
"""

from collections import deque
from typing import Optional


# ── PERCEPTION ────────────────────────────────────────────────────────────────

def background(grid: list) -> int:
    """Most common color in grid."""
    counts = {}
    for row in grid:
        for c in row:
            counts[c] = counts.get(c, 0) + 1
    return max(counts, key=counts.get)


def palette(grid: list, include_bg: bool = False) -> set:
    """All colors used in grid. Excludes background unless include_bg=True."""
    colors = {c for row in grid for c in row}
    if not include_bg:
        colors.discard(background(grid))
    return colors


def cells_of_color(grid: list, color: int) -> list:
    """All (row, col) positions of the given color."""
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]


def find_objects(grid: list, bg: int = 0, connectivity: int = 4) -> list:
    """
    Connected components of same non-bg color.
    Returns list of cell-lists; each cell is (row, col).
    connectivity=4 (cardinal) or 8 (including diagonals).
    """
    n_rows, n_cols = len(grid), len(grid[0])
    visited = [[False] * n_cols for _ in range(n_rows)]
    objects = []

    def neighbors(r, c):
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        if connectivity == 8:
            dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        return [(r+dr, c+dc) for dr, dc in dirs
                if 0 <= r+dr < n_rows and 0 <= c+dc < n_cols]

    for r in range(n_rows):
        for c in range(n_cols):
            if grid[r][c] != bg and not visited[r][c]:
                color = grid[r][c]
                queue = deque([(r, c)])
                visited[r][c] = True
                cells = []
                while queue:
                    cr, cc = queue.popleft()
                    cells.append((cr, cc))
                    for nr, nc in neighbors(cr, cc):
                        if not visited[nr][nc] and grid[nr][nc] == color:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                objects.append(cells)
    return objects


def bounding_box(cells: list) -> tuple:
    """(min_row, min_col, max_row, max_col) inclusive."""
    rows = [r for r, c in cells]
    cols = [c for r, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def find_lines(grid: list, direction: str = 'h') -> list:
    """
    Row indices (direction='h') or col indices (direction='v')
    that are entirely one non-background color.
    """
    n_rows, n_cols = len(grid), len(grid[0])
    bg = background(grid)
    result = []
    if direction == 'h':
        for r in range(n_rows):
            colors = set(grid[r])
            if len(colors) == 1 and bg not in colors:
                result.append(r)
    else:
        for c in range(n_cols):
            colors = {grid[r][c] for r in range(n_rows)}
            if len(colors) == 1 and bg not in colors:
                result.append(c)
    return result


def color_at(grid: list, r: int, c: int) -> int:
    """Color at (r, c); returns 0 if out of bounds."""
    if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
        return grid[r][c]
    return 0


def neighbors_4(r: int, c: int, n_rows: int, n_cols: int) -> list:
    """4-connected neighbors within bounds."""
    return [(r+dr, c+dc) for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
            if 0 <= r+dr < n_rows and 0 <= c+dc < n_cols]


def neighbors_8(r: int, c: int, n_rows: int, n_cols: int) -> list:
    """8-connected neighbors within bounds."""
    return [(r+dr, c+dc)
            for dr in [-1,0,1] for dc in [-1,0,1]
            if (dr, dc) != (0, 0)
            and 0 <= r+dr < n_rows and 0 <= c+dc < n_cols]


def grid_size(grid: list) -> tuple:
    """(n_rows, n_cols)."""
    return len(grid), len(grid[0])


# ── GEOMETRY ──────────────────────────────────────────────────────────────────

def new_grid(n_rows: int, n_cols: int, fill: int = 0) -> list:
    """Create a new grid filled with a single value."""
    return [[fill] * n_cols for _ in range(n_rows)]


def copy_grid(grid: list) -> list:
    """Deep copy a grid."""
    return [row[:] for row in grid]


def crop(grid: list, r1: int, c1: int, r2: int, c2: int) -> list:
    """Crop grid to (r1,c1)–(r2,c2) inclusive."""
    return [row[c1:c2+1] for row in grid[r1:r2+1]]


def rotate(grid: list, deg: int = 90) -> list:
    """Rotate grid clockwise by deg degrees (90, 180, or 270)."""
    g = grid
    times = (deg // 90) % 4
    for _ in range(times):
        g = [list(row) for row in zip(*g[::-1])]
    return g


def flip(grid: list, axis: str = 'h') -> list:
    """
    Flip grid. axis='h' = left-right (horizontal mirror).
    axis='v' = top-bottom (vertical mirror).
    """
    if axis == 'h':
        return [row[::-1] for row in grid]
    else:
        return grid[::-1]


def scale_up(grid: list, factor: int) -> list:
    """Each cell becomes a factor×factor block."""
    result = []
    for row in grid:
        expanded_row = [v for v in row for _ in range(factor)]
        for _ in range(factor):
            result.append(expanded_row[:])
    return result


def scale_down(grid: list, factor: int) -> list:
    """Keep every Nth row and col (factor=2 → half size)."""
    return [row[::factor] for row in grid[::factor]]


def tile(subgrid: list, n_rows: int, n_cols: int) -> list:
    """Repeat subgrid to fill exactly n_rows × n_cols."""
    sh, sw = len(subgrid), len(subgrid[0])
    result = new_grid(n_rows, n_cols)
    for r in range(n_rows):
        for c in range(n_cols):
            result[r][c] = subgrid[r % sh][c % sw]
    return result


def pad(grid: list, value: int = 0, top: int = 0, bottom: int = 0,
        left: int = 0, right: int = 0) -> list:
    """Add padding around the grid."""
    n_rows, n_cols = len(grid), len(grid[0])
    new_cols = n_cols + left + right
    result = []
    for _ in range(top):
        result.append([value] * new_cols)
    for row in grid:
        result.append([value] * left + row[:] + [value] * right)
    for _ in range(bottom):
        result.append([value] * new_cols)
    return result


def paste(base: list, overlay: list, r: int, c: int, transparent: int = 0) -> list:
    """
    Overlay subgrid onto base at top-left (r, c).
    Cells in overlay equal to transparent are skipped.
    """
    result = copy_grid(base)
    for dr, row in enumerate(overlay):
        for dc, val in enumerate(row):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(result) and 0 <= nc < len(result[0]):
                if val != transparent:
                    result[nr][nc] = val
    return result


# ── DRAWING ───────────────────────────────────────────────────────────────────

def draw_rect(grid: list, r1: int, c1: int, r2: int, c2: int,
              color: int, fill: bool = False) -> list:
    """Rectangle border or filled rectangle."""
    result = copy_grid(grid)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if fill or r in (r1, r2) or c in (c1, c2):
                if 0 <= r < len(result) and 0 <= c < len(result[0]):
                    result[r][c] = color
    return result


def draw_cross(grid: list, r: int, c: int, color: int, size: int = 1) -> list:
    """Plus-shape: center + size cells in each cardinal direction."""
    result = copy_grid(grid)
    n_rows, n_cols = len(grid), len(grid[0])
    for dr in range(-size, size + 1):
        if 0 <= r + dr < n_rows:
            result[r + dr][c] = color
    for dc in range(-size, size + 1):
        if 0 <= c + dc < n_cols:
            result[r][c + dc] = color
    return result


def draw_line(grid: list, r1: int, c1: int, r2: int, c2: int, color: int) -> list:
    """Bresenham line from (r1,c1) to (r2,c2)."""
    result = copy_grid(grid)
    n_rows, n_cols = len(grid), len(grid[0])
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        if 0 <= r < n_rows and 0 <= c < n_cols:
            result[r][c] = color
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return result


def trace_ray(grid: list, r: int, c: int, dr: int, dc: int,
              stop_colors: Optional[set] = None) -> list:
    """
    From (r,c) step by (dr,dc) until boundary or hitting stop_colors.
    Returns list of (row,col) cells visited (not including start).
    """
    n_rows, n_cols = len(grid), len(grid[0])
    cells = []
    nr, nc = r + dr, c + dc
    while 0 <= nr < n_rows and 0 <= nc < n_cols:
        if stop_colors and grid[nr][nc] in stop_colors:
            break
        cells.append((nr, nc))
        nr += dr
        nc += dc
    return cells


def fill_region(grid: list, r: int, c: int, color: int) -> list:
    """Flood-fill from (r,c), replacing that cell's original color with new color."""
    result = copy_grid(grid)
    n_rows, n_cols = len(grid), len(grid[0])
    target = result[r][c]
    if target == color:
        return result
    queue = deque([(r, c)])
    result[r][c] = color
    while queue:
        cr, cc = queue.popleft()
        for nr, nc in neighbors_4(cr, cc, n_rows, n_cols):
            if result[nr][nc] == target:
                result[nr][nc] = color
                queue.append((nr, nc))
    return result


# ── COLOR ─────────────────────────────────────────────────────────────────────

def replace_color(grid: list, old_color: int, new_color: int) -> list:
    """Replace all occurrences of old_color with new_color."""
    return [[new_color if v == old_color else v for v in row] for row in grid]


def map_colors(grid: list, mapping: dict) -> list:
    """Apply color mapping dict; unmapped colors are unchanged."""
    return [[mapping.get(v, v) for v in row] for row in grid]


# ── LOGIC ─────────────────────────────────────────────────────────────────────

def count_color(grid: list, color: int) -> int:
    """Count cells of given color."""
    return sum(v == color for row in grid for v in row)


def grid_equals(g1: list, g2: list) -> bool:
    """True if grids are identical."""
    if len(g1) != len(g2) or len(g1[0]) != len(g2[0]):
        return False
    return all(g1[r][c] == g2[r][c]
               for r in range(len(g1)) for c in range(len(g1[0])))


def grid_diff(g1: list, g2: list) -> list:
    """Return list of (r, c, expected, got) for differing cells."""
    diffs = []
    for r in range(min(len(g1), len(g2))):
        for c in range(min(len(g1[r]), len(g2[r]))):
            if g1[r][c] != g2[r][c]:
                diffs.append((r, c, g1[r][c], g2[r][c]))
    if len(g1) != len(g2):
        diffs.append(('size', len(g1), len(g2), None))
    return diffs


def apply_to_objects(grid: list, func, bg: int = 0) -> list:
    """
    Find all objects, apply func(subgrid) to each object's bounding box,
    paste results back. func receives the cropped subgrid and returns a new one.
    """
    result = copy_grid(grid)
    for obj_cells in find_objects(grid, bg=bg):
        r1, c1, r2, c2 = bounding_box(obj_cells)
        subgrid = crop(grid, r1, c1, r2, c2)
        transformed = func(subgrid)
        result = paste(result, transformed, r1, c1)
    return result


def nearest_cell(origin: tuple, cells: list) -> Optional[tuple]:
    """From origin=(r,c), find nearest cell by Manhattan distance."""
    if not cells:
        return None
    return min(cells, key=lambda cell: abs(cell[0]-origin[0]) + abs(cell[1]-origin[1]))


def object_color(grid: list, cells: list) -> int:
    """Color of the first cell in the object."""
    r, c = cells[0]
    return grid[r][c]


# ── COMPOSITION ───────────────────────────────────────────────────────────────

def compose(*funcs):
    """
    Returns a function that applies funcs left-to-right.
    compose(f, g)(x) == g(f(x))
    """
    def composed(x):
        for f in funcs:
            x = f(x)
        return x
    return composed


# ── DISPLAY HELPERS ───────────────────────────────────────────────────────────

_CHARS = '.abcdefghi'

def display(grid: list, label: str = '') -> None:
    """Print grid using color characters for readability."""
    if label:
        print(f'[{label}]')
    for row in grid:
        print(' '.join(_CHARS[v] if v < len(_CHARS) else str(v) for v in row))
    print()


# ── SELF-TESTS ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    passed = 0
    failed = 0

    def check(name, got, expected):
        global passed, failed
        if got == expected:
            print(f'  PASS: {name}')
            passed += 1
        else:
            print(f'  FAIL: {name}')
            print(f'    got:      {got}')
            print(f'    expected: {expected}')
            failed += 1

    print('=== arc_dsl.py self-tests ===\n')

    # 1. rotate 90°
    g = [[1, 2, 3],
         [4, 5, 6]]
    check('rotate 90°', rotate(g, 90), [[4, 1], [5, 2], [6, 3]])
    check('rotate 180°', rotate(g, 180), [[6, 5, 4], [3, 2, 1]])

    # 2. flip
    check('flip h', flip([[1,2,3],[4,5,6]], 'h'), [[3,2,1],[6,5,4]])
    check('flip v', flip([[1,2,3],[4,5,6]], 'v'), [[4,5,6],[1,2,3]])

    # 3. find_objects
    g2 = [[1,1,0,2],
          [1,0,0,2],
          [0,0,3,0]]
    objs = find_objects(g2, bg=0)
    sizes = sorted(len(o) for o in objs)
    check('find_objects sizes', sizes, [1, 2, 3])

    # 4. draw_cross
    g3 = new_grid(5, 5)
    result = draw_cross(g3, 2, 2, 1, size=1)
    cross_cells = [(r,c) for r in range(5) for c in range(5) if result[r][c] == 1]
    check('draw_cross cells', sorted(cross_cells),
          sorted([(1,2),(2,1),(2,2),(2,3),(3,2)]))

    # 5. tile
    sub = [[1,2],[3,4]]
    tiled = tile(sub, 4, 4)
    check('tile 2x2→4x4', tiled, [[1,2,1,2],[3,4,3,4],[1,2,1,2],[3,4,3,4]])

    # 6. map_colors
    g4 = [[1,2,1],[2,1,2]]
    check('map_colors', map_colors(g4, {1:5, 2:6}), [[5,6,5],[6,5,6]])

    # 7. trace_ray
    g5 = new_grid(5, 5)
    ray = trace_ray(g5, 0, 0, 1, 1)  # diagonal down-right
    check('trace_ray diagonal', ray, [(1,1),(2,2),(3,3),(4,4)])

    # 8. bounding_box
    check('bounding_box', bounding_box([(1,2),(3,4),(2,1)]), (1,1,3,4))

    # 9. scale_up
    check('scale_up x2', scale_up([[1,2],[3,4]], 2),
          [[1,1,2,2],[1,1,2,2],[3,3,4,4],[3,3,4,4]])

    # 10. crop
    g6 = [[1,2,3],[4,5,6],[7,8,9]]
    check('crop', crop(g6, 0, 1, 1, 2), [[2,3],[5,6]])

    # 11. background
    g7 = [[0,0,1],[0,1,0],[1,0,0]]
    check('background', background(g7), 0)

    # 12. grid_diff
    a = [[1,2],[3,4]]
    b = [[1,9],[3,4]]
    check('grid_diff', grid_diff(a, b), [(0, 1, 2, 9)])

    # 13. fill_region
    g8 = [[1,1,1],[1,0,1],[1,1,1]]
    filled = fill_region(g8, 1, 1, 5)
    check('fill_region', filled[1][1], 5)
    check('fill_region no spill', filled[0][0], 1)

    # 14. compose
    double = lambda g: scale_up(g, 2)
    fliph  = lambda g: flip(g, 'h')
    pipeline = compose(double, fliph)
    result2 = pipeline([[1,2],[3,4]])
    check('compose', result2, [[2,2,1,1],[2,2,1,1],[4,4,3,3],[4,4,3,3]])

    print(f'\n{passed} passed, {failed} failed')
