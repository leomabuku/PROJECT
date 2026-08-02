from __future__ import annotations

from gui.ast_canvas import layout_ast_tree
from gui.ast_tree import ast_node_category, build_ast_tree_rows
from tongalang.parser import parse_source


def _sample_rows():
    return build_ast_tree_rows(
        parse_source(
            """
            mulimo matalikilo() {
                zina x = 1 + 2 * 3
                kuti (x inda 3) { amba(x) } nakunyina { amba(0) }
            }
            """
        )
    )


def test_layout_is_deterministic():
    rows = _sample_rows()
    assert layout_ast_tree(rows) == layout_ast_tree(rows)


def test_every_parent_is_above_its_children():
    rows = _sample_rows()
    layout = layout_ast_tree(rows)
    for row in rows:
        if row.parent_id:
            assert layout[row.parent_id].y < layout[row.node_id].y


def test_parent_centres_between_outermost_children():
    rows = _sample_rows()
    layout = layout_ast_tree(rows)
    children = [row for row in rows if row.parent_id == rows[0].node_id]
    parent = layout[rows[0].node_id]
    parent_center = parent.x + parent.width / 2
    child_centers = [layout[row.node_id].x + layout[row.node_id].width / 2 for row in children]
    assert parent_center == (child_centers[0] + child_centers[-1]) / 2


def test_empty_layout_is_safe():
    assert layout_ast_tree([]) == {}


def test_rows_record_depth_and_source_locations():
    rows = _sample_rows()
    assert rows[0].depth == 0
    assert max(row.depth for row in rows) >= 5
    assert all(row.line is not None for row in rows)


def test_visual_categories_cover_core_node_roles():
    assert ast_node_category("Program") == "root"
    assert ast_node_category("VarDecl") == "declaration"
    assert ast_node_category("IfStmt") == "control"
    assert ast_node_category("Binary") == "expression"
    assert ast_node_category("Literal") == "value"
