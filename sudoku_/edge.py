from typing import List, Set

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter

from sudoku_.sudoku import Cell
from utils import Constants


class Edge:
    def __init__(self, sx: int, sy: int, ex: int, ey: int, edge_type: int):

        self.sx = sx
        self.sy = sy
        self.ex = ex
        self.ey = ey

        self.id_ = None
        self.edge_type = edge_type

    def __repr__(self):
        return f"({self.sx}, {self.sy}) -> ({self.ex}, {self.ey})"

    def draw(self, painter: QPainter, cell_size: int, offset: int):
        if self.edge_type == Constants.NORTH:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey + offset
            )

        elif self.edge_type == Constants.EAST:
            painter.drawLine(
                cell_size + self.sx - offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey - offset
            )

        elif self.edge_type == Constants.SOUTH:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy - offset,
                cell_size + self.ex - offset,
                cell_size + self.ey - offset
            )

        else:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy + offset,
                cell_size + self.ex + offset,
                cell_size + self.ey - offset
            )


def tile_to_poly(cells: List[Cell], cell_size: int, selected: Set, inner_offset: int):
    edges = []

    selected = {QPoint(i % 9, i // 9) for i in selected}

    for cell in cells:
        cell.reset()

    for i in range(81):

        p = get_point(i)
        if p not in selected:
            continue

        north = QPoint(p.x(), p.y() - 1)
        north_east = QPoint(p.x() + 1, p.y() - 1)

        east = QPoint(p.x() + 1, p.y())
        south_east = QPoint(p.x() + 1, p.y() + 1)

        south = QPoint(p.x(), p.y() + 1)
        south_west = QPoint(p.x() - 1, p.y() + 1)

        west = QPoint(p.x() - 1, p.y())
        north_west = QPoint(p.x() - 1, p.y() - 1)

        if west not in selected:
            if cells[get_index(north)].edge_exists[Constants.WEST]:

                edges[cells[get_index(north)].edge_id[Constants.WEST]].ey += cell_size
                cells[i].edge_id[Constants.WEST] = cells[get_index(north)].edge_id[Constants.WEST]
                cells[i].edge_exists[Constants.WEST] = True

            else:

                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, Constants.WEST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.WEST] = edge.id_
                cells[i].edge_exists[Constants.WEST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if south in selected and south_west in selected:
                edges[cells[i].edge_id[Constants.WEST]].ey += inner_offset * 2

            if north in selected and north_west in selected:
                edges[cells[i].edge_id[Constants.WEST]].sy -= inner_offset * 2

        if north not in selected:

            if (cells[get_index(west)].edge_exists[Constants.NORTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[Constants.NORTH]].ex += cell_size
                cells[i].edge_id[Constants.NORTH] = cells[get_index(west)].edge_id[Constants.NORTH]
                cells[i].edge_exists[Constants.NORTH] = True

            else:
                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, Constants.NORTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.NORTH] = edge.id_
                cells[i].edge_exists[Constants.NORTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and north_east in selected:
                edges[cells[i].edge_id[Constants.NORTH]].ex += inner_offset * 2

            if west in selected and north_west in selected:
                edges[cells[i].edge_id[Constants.NORTH]].sx -= inner_offset * 2

        if east not in selected:
            if cells[get_index(north)].edge_exists[Constants.EAST]:
                edges[cells[get_index(north)].edge_id[Constants.EAST]].ey += cell_size
                cells[i].edge_id[Constants.EAST] = cells[get_index(north)].edge_id[Constants.EAST]
                cells[i].edge_exists[Constants.EAST] = True

            else:
                sx = (1 + p.x()) * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, Constants.EAST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.EAST] = edge.id_
                cells[i].edge_exists[Constants.EAST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if north in selected and north_east in selected:
                edges[cells[i].edge_id[Constants.EAST]].sy -= inner_offset * 2

            if south in selected and south_east in selected:
                edges[cells[i].edge_id[Constants.EAST]].ey += inner_offset * 2

        if south not in selected:
            if (cells[get_index(west)].edge_exists[Constants.SOUTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[Constants.SOUTH]].ex += cell_size
                cells[i].edge_id[Constants.SOUTH] = cells[get_index(west)].edge_id[Constants.SOUTH]
                cells[i].edge_exists[Constants.SOUTH] = True

            else:
                sx = p.x() * cell_size
                sy = (1 + p.y()) * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, Constants.SOUTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.SOUTH] = edge.id_
                cells[i].edge_exists[Constants.SOUTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and south_east in selected:
                edges[cells[i].edge_id[Constants.SOUTH]].ex += inner_offset * 2

            if west in selected and south_west in selected:
                edges[cells[i].edge_id[Constants.SOUTH]].sx -= inner_offset * 2

    return edges


def get_index(p: QPoint) -> int:
    return p.y() * 9 + p.x()


def get_point(index: int) -> QPoint:
    return QPoint(index % 9, index // 9)


def valid(p: QPoint) -> bool:
    return 0 <= p.y() * 9 + p.x() <= 81
