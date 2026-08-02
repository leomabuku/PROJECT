from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable

from .ast_tree import ASTTreeNode, ast_node_category


@dataclass(frozen=True)
class ASTLayoutNode:
    node_id: str
    x: float
    y: float
    width: float
    height: float
    depth: int


def layout_ast_tree(
    rows: Iterable[ASTTreeNode],
    *,
    node_width: float = 210,
    node_height: float = 58,
    horizontal_gap: float = 34,
    vertical_gap: float = 62,
) -> dict[str, ASTLayoutNode]:
    """Lay out a rooted AST with parents centred above their children."""
    row_list = list(rows)
    if not row_list:
        return {}

    row_by_id = {row.node_id: row for row in row_list}
    children: dict[str, list[str]] = {row.node_id: [] for row in row_list}
    roots: list[str] = []
    for row in row_list:
        if row.parent_id and row.parent_id in children:
            children[row.parent_id].append(row.node_id)
        else:
            roots.append(row.node_id)

    next_leaf_x = 0.0
    centers: dict[str, float] = {}

    def place(node_id: str) -> float:
        nonlocal next_leaf_x
        child_ids = children[node_id]
        if not child_ids:
            center = next_leaf_x + node_width / 2
            next_leaf_x += node_width + horizontal_gap
        else:
            child_centers = [place(child_id) for child_id in child_ids]
            center = (child_centers[0] + child_centers[-1]) / 2
        centers[node_id] = center
        return center

    for root_id in roots:
        place(root_id)
        next_leaf_x += horizontal_gap * 2

    min_center = min(centers.values())
    offset = 24 - (min_center - node_width / 2)
    return {
        node_id: ASTLayoutNode(
            node_id=node_id,
            x=center - node_width / 2 + offset,
            y=24 + row_by_id[node_id].depth * (node_height + vertical_gap),
            width=node_width,
            height=node_height,
            depth=row_by_id[node_id].depth,
        )
        for node_id, center in centers.items()
    }


class ASTCanvas(ttk.Frame):
    """Scrollable, zoomable AST diagram with selectable nodes."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        on_select: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.on_select = on_select
        self.rows: dict[str, ASTTreeNode] = {}
        self.layout: dict[str, ASTLayoutNode] = {}
        self.scale = 1.0
        self.selected_id: str | None = None
        self.palette = {
            "canvas": "#0f172a",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "line": "#475569",
            "outline": "#64748b",
            "selected": "#60a5fa",
            "root": "#1d4ed8",
            "declaration": "#0f766e",
            "control": "#7c3aed",
            "expression": "#9a3412",
            "value": "#334155",
            "structure": "#1f2937",
        }

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, background=self.palette["canvas"])
        self.xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.yscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.xscroll.set, yscrollcommand=self.yscroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.yscroll.grid(row=0, column=1, sticky="ns")
        self.xscroll.grid(row=1, column=0, sticky="ew")

        self.canvas.bind("<Control-MouseWheel>", self._zoom_wheel)
        self.canvas.bind("<MouseWheel>", self._scroll_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self._horizontal_wheel)
        self.canvas.bind("<ButtonPress-2>", lambda event: self.canvas.scan_mark(event.x, event.y))
        self.canvas.bind("<B2-Motion>", lambda event: self.canvas.scan_dragto(event.x, event.y, gain=1))

    def set_palette(self, palette: dict[str, str]) -> None:
        self.palette.update(palette)
        self.canvas.configure(background=self.palette["canvas"])
        self.redraw()

    def set_rows(self, rows: Iterable[ASTTreeNode]) -> None:
        row_list = list(rows)
        self.rows = {row.node_id: row for row in row_list}
        self.layout = layout_ast_tree(row_list)
        self.selected_id = None
        # Start at a legible scale and centre the root.  A complete AST can be
        # much wider than the viewport; shrinking it until every leaf fits made
        # labels unreadable and visually merged neighbouring nodes.
        self.scale = 0.65
        self.redraw()
        self._focus_root()

    def redraw(self) -> None:
        self.canvas.delete("all")
        if not self.rows:
            self.canvas.create_text(
                28,
                28,
                anchor="nw",
                text="Run or refresh a program to build its syntax tree.",
                fill=self.palette["muted"],
                font=("Segoe UI", 11),
            )
            return

        for row in self.rows.values():
            if not row.parent_id or row.parent_id not in self.layout:
                continue
            parent = self.layout[row.parent_id]
            child = self.layout[row.node_id]
            x1 = (parent.x + parent.width / 2) * self.scale
            y1 = (parent.y + parent.height) * self.scale
            x2 = (child.x + child.width / 2) * self.scale
            y2 = child.y * self.scale
            mid_y = (y1 + y2) / 2
            self.canvas.create_line(
                x1,
                y1,
                x1,
                mid_y,
                x2,
                mid_y,
                x2,
                y2,
                fill=self.palette["line"],
                width=max(1, int(2 * self.scale)),
                smooth=False,
                tags=("edge",),
            )

        for row in self.rows.values():
            box = self.layout[row.node_id]
            self._draw_node(row, box)

        self.canvas.tag_lower("edge")
        bounds = self.canvas.bbox("all")
        if bounds:
            self.canvas.configure(scrollregion=(bounds[0] - 30, bounds[1] - 30, bounds[2] + 30, bounds[3] + 30))

    def _draw_node(self, row: ASTTreeNode, box: ASTLayoutNode) -> None:
        x1, y1 = box.x * self.scale, box.y * self.scale
        x2 = (box.x + box.width) * self.scale
        y2 = (box.y + box.height) * self.scale
        category = ast_node_category(row.node_type)
        selected = row.node_id == self.selected_id
        outline = self.palette["selected"] if selected else self.palette["outline"]
        width = 3 if selected else 1
        tags = ("node", row.node_id)
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=self.palette.get(category, self.palette["structure"]),
            outline=outline,
            width=width,
            tags=tags,
        )
        label = row.label if len(row.label) <= 34 else row.label[:31] + "..."
        self.canvas.create_text(
            (x1 + x2) / 2,
            y1 + 20 * self.scale,
            text=label,
            fill="#ffffff",
            font=("Segoe UI", max(5, int(10 * self.scale)), "bold"),
            width=max(80, int((box.width - 16) * self.scale)),
            tags=tags,
        )
        location = "" if row.line is None else f"line {row.line}"
        subtitle = row.node_type if not location else f"{row.node_type}  |  {location}"
        self.canvas.create_text(
            (x1 + x2) / 2,
            y2 - 14 * self.scale,
            text=subtitle,
            fill="#dbeafe",
            font=("Segoe UI", max(4, int(8 * self.scale))),
            tags=tags,
        )
        self.canvas.tag_bind(row.node_id, "<Button-1>", lambda _event, node_id=row.node_id: self.select(node_id))
        self.canvas.tag_bind(row.node_id, "<Double-Button-1>", lambda _event, node_id=row.node_id: self.select(node_id))

    def select(self, node_id: str) -> None:
        if node_id not in self.rows:
            return
        self.selected_id = node_id
        self.redraw()
        if self.on_select is not None:
            self.on_select(node_id)

    def set_zoom(self, scale: float) -> None:
        self.scale = max(0.35, min(1.8, scale))
        self.redraw()

    def zoom_in(self) -> None:
        self.set_zoom(self.scale + 0.1)

    def zoom_out(self) -> None:
        self.set_zoom(self.scale - 0.1)

    def fit_to_window(self) -> None:
        if not self.layout:
            return
        self.update_idletasks()
        max_x = max(node.x + node.width for node in self.layout.values()) + 48
        max_y = max(node.y + node.height for node in self.layout.values()) + 48
        viewport_w = max(1, self.canvas.winfo_width())
        viewport_h = max(1, self.canvas.winfo_height())
        self.scale = max(0.35, min(1.0, min(viewport_w / max_x, viewport_h / max_y)))
        self.redraw()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def _focus_root(self) -> None:
        """Place the root near the horizontal centre without hiding detail."""
        if not self.layout:
            return
        self.update_idletasks()
        roots = [row for row in self.rows.values() if not row.parent_id]
        if not roots:
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            return
        root_box = self.layout[roots[0].node_id]
        bounds = self.canvas.bbox("all")
        if not bounds:
            return
        left, _top, right, _bottom = bounds
        content_width = max(1.0, right - left)
        viewport_width = max(1.0, self.canvas.winfo_width())
        root_center = (root_box.x + root_box.width / 2) * self.scale
        desired_left = root_center - viewport_width / 2
        fraction = (desired_left - left) / content_width
        self.canvas.xview_moveto(max(0.0, min(1.0, fraction)))
        self.canvas.yview_moveto(0)

    def _zoom_wheel(self, event: tk.Event) -> str:
        self.set_zoom(self.scale + (0.1 if event.delta > 0 else -0.1))
        return "break"

    def _scroll_wheel(self, event: tk.Event) -> str:
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def _horizontal_wheel(self, event: tk.Event) -> str:
        self.canvas.xview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"
