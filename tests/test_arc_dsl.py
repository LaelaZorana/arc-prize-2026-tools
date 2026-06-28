"""Unit tests for the ARC DSL primitives.

These mirror (and extend) the in-module self-tests, but as real pytest cases so
CI exercises the whole grid-operation surface on every change.
"""
from __future__ import annotations

import arc_dsl as d


# ── perception ──────────────────────────────────────────────────────────────

def test_background_is_most_common_color():
    assert d.background([[0, 0, 1], [0, 1, 0], [1, 0, 0]]) == 0
    assert d.background([[5, 5, 5], [5, 2, 5]]) == 5


def test_palette_excludes_background_by_default():
    grid = [[0, 1, 2], [0, 1, 0]]
    assert d.palette(grid) == {1, 2}
    assert d.palette(grid, include_bg=True) == {0, 1, 2}


def test_cells_of_color():
    grid = [[1, 0], [0, 1]]
    assert sorted(d.cells_of_color(grid, 1)) == [(0, 0), (1, 1)]
    assert d.cells_of_color(grid, 7) == []


def test_find_objects_sizes_and_connectivity():
    grid = [[1, 1, 0, 2],
            [1, 0, 0, 2],
            [0, 0, 3, 0]]
    sizes = sorted(len(o) for o in d.find_objects(grid, bg=0))
    assert sizes == [1, 2, 3]
    # Diagonal touch only merges under 8-connectivity.
    diag = [[4, 0], [0, 4]]
    assert len(d.find_objects(diag, bg=0, connectivity=4)) == 2
    assert len(d.find_objects(diag, bg=0, connectivity=8)) == 1


def test_bounding_box():
    assert d.bounding_box([(1, 2), (3, 4), (2, 1)]) == (1, 1, 3, 4)


def test_find_lines():
    # Background must be an unambiguous 0, so the all-2 and all-3 rows read as lines.
    grid = [[2, 2, 2],
            [0, 5, 0],
            [3, 3, 3],
            [0, 0, 0],
            [0, 0, 0]]
    assert d.find_lines(grid, "h") == [0, 2]
    col = [[7, 0, 0],
           [7, 0, 0],
           [7, 0, 0]]
    assert d.find_lines(col, "v") == [0]


def test_color_at_handles_out_of_bounds():
    grid = [[1, 2], [3, 4]]
    assert d.color_at(grid, 0, 1) == 2
    assert d.color_at(grid, 9, 9) == 0
    assert d.color_at(grid, -1, 0) == 0


def test_grid_size():
    assert d.grid_size([[0, 0, 0], [0, 0, 0]]) == (2, 3)


# ── geometry ────────────────────────────────────────────────────────────────

def test_rotate():
    g = [[1, 2, 3], [4, 5, 6]]
    assert d.rotate(g, 90) == [[4, 1], [5, 2], [6, 3]]
    assert d.rotate(g, 180) == [[6, 5, 4], [3, 2, 1]]
    assert d.rotate(g, 360) == g


def test_flip():
    g = [[1, 2, 3], [4, 5, 6]]
    assert d.flip(g, "h") == [[3, 2, 1], [6, 5, 4]]
    assert d.flip(g, "v") == [[4, 5, 6], [1, 2, 3]]


def test_crop():
    g = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert d.crop(g, 0, 1, 1, 2) == [[2, 3], [5, 6]]


def test_scale_up_and_down_roundtrip():
    g = [[1, 2], [3, 4]]
    up = d.scale_up(g, 2)
    assert up == [[1, 1, 2, 2], [1, 1, 2, 2], [3, 3, 4, 4], [3, 3, 4, 4]]
    assert d.scale_down(up, 2) == g


def test_tile():
    assert d.tile([[1, 2], [3, 4]], 4, 4) == [
        [1, 2, 1, 2], [3, 4, 3, 4], [1, 2, 1, 2], [3, 4, 3, 4]
    ]


def test_pad():
    out = d.pad([[5]], value=0, top=1, bottom=1, left=2, right=0)
    assert out == [[0, 0, 0], [0, 0, 5], [0, 0, 0]]


def test_paste_respects_transparency():
    base = d.new_grid(3, 3, 0)
    overlay = [[7, 0], [0, 7]]
    out = d.paste(base, overlay, 0, 0, transparent=0)
    assert out[0][0] == 7 and out[1][1] == 7
    assert out[0][1] == 0  # transparent cell left untouched


# ── drawing ─────────────────────────────────────────────────────────────────

def test_draw_rect_border_vs_fill():
    border = d.draw_rect(d.new_grid(4, 4), 0, 0, 3, 3, 1, fill=False)
    assert border[1][1] == 0 and border[0][0] == 1 and border[3][3] == 1
    filled = d.draw_rect(d.new_grid(4, 4), 0, 0, 3, 3, 1, fill=True)
    assert all(v == 1 for row in filled for v in row)


def test_draw_cross():
    out = d.draw_cross(d.new_grid(5, 5), 2, 2, 1, size=1)
    on = sorted((r, c) for r in range(5) for c in range(5) if out[r][c] == 1)
    assert on == [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)]


def test_draw_line_diagonal():
    out = d.draw_line(d.new_grid(3, 3), 0, 0, 2, 2, 1)
    assert out[0][0] == 1 and out[1][1] == 1 and out[2][2] == 1


def test_trace_ray_stops_on_color():
    g = d.new_grid(5, 5)
    g[0][3] = 9
    ray = d.trace_ray(g, 0, 0, 0, 1, stop_colors={9})
    assert ray == [(0, 1), (0, 2)]


def test_fill_region_no_spill():
    g = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
    out = d.fill_region(g, 1, 1, 5)
    assert out[1][1] == 5
    assert out[0][0] == 1  # outer ring of a different color is untouched


# ── color / logic / composition ──────────────────────────────────────────────

def test_replace_and_map_colors():
    assert d.replace_color([[1, 2], [2, 1]], 2, 9) == [[1, 9], [9, 1]]
    assert d.map_colors([[1, 2, 1]], {1: 5, 2: 6}) == [[5, 6, 5]]


def test_count_color():
    assert d.count_color([[1, 1, 0], [1, 0, 0]], 1) == 3


def test_grid_equals_and_diff():
    a = [[1, 2], [3, 4]]
    assert d.grid_equals(a, [[1, 2], [3, 4]])
    assert not d.grid_equals(a, [[1, 2]])
    assert d.grid_diff(a, [[1, 9], [3, 4]]) == [(0, 1, 2, 9)]


def test_compose_applies_left_to_right():
    pipeline = d.compose(lambda g: d.scale_up(g, 2), lambda g: d.flip(g, "h"))
    assert pipeline([[1, 2], [3, 4]]) == [
        [2, 2, 1, 1], [2, 2, 1, 1], [4, 4, 3, 3], [4, 4, 3, 3]
    ]


def test_nearest_cell_and_object_color():
    assert d.nearest_cell((0, 0), [(5, 5), (1, 1)]) == (1, 1)
    assert d.nearest_cell((0, 0), []) is None
    assert d.object_color([[0, 0], [0, 7]], [(1, 1)]) == 7


def test_apply_to_objects_transforms_each_object():
    # Two single-cell objects; identity transform must preserve them.
    grid = [[1, 0, 2]]
    assert d.apply_to_objects(grid, lambda sub: sub, bg=0) == grid
