from typing import List, Tuple, Set

from PySide6.QtCore import QPoint

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3


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

    def start(self, offset: int):
        if self.edge_type == WEST:
            return QPoint(self.sx + offset, self.sy)
        elif self.edge_type == EAST:
            return QPoint(self.sx - offset, self.sy)
        elif self.edge_type == NORTH:
            return QPoint(self.sx, self.sy + offset)
        elif self.edge_type == SOUTH:
            return QPoint(self.sx, self.sy - offset)

    def end(self, offset: int):
        if self.edge_type == WEST:
            return QPoint(self.ex + offset, self.ey)
        elif self.edge_type == EAST:
            return QPoint(self.ex - offset, self.ey)
        elif self.edge_type == NORTH:
            return QPoint(self.ex, self.ey + offset)
        elif self.edge_type == SOUTH:
            return QPoint(self.ex, self.ey - offset)


def tile_to_poly(cells: List, cell_size: int, selected: Set):
    edges = []

    for cell in cells:
        cell.reset()

    for i in range(81):

        p = get_point(i)

        north = QPoint(p.x(), p.y() - 1)
        south = QPoint(p.x(), p.y() + 1)
        west = QPoint(p.x() - 1, p.y())
        east = QPoint(p.x() + 1, p.y())

        if p in selected:
            if west not in selected:
                if cells[get_index(north)].edge_exists[WEST]:
                    edges[cells[get_index(north)].edge_id[WEST]].ey += cell_size
                    cells[i].edge_id[WEST] = cells[get_index(north)].edge_id[WEST]
                    cells[i].edge_exists[WEST] = True

                else:
                    sx = p.x() * cell_size
                    sy = p.y() * cell_size
                    ex, ey = sx, sy + cell_size
                    edge = Edge(sx, sy, ex, ey, WEST)

                    edge.id_ = len(edges)
                    edges.append(edge)

                    cells[i].edge_id[WEST] = edge.id_
                    cells[i].edge_exists[WEST] = True

            if east not in selected:
                if cells[get_index(north)].edge_exists[EAST]:
                    edges[cells[get_index(north)].edge_id[EAST]].ey += cell_size
                    cells[i].edge_id[EAST] = cells[get_index(north)].edge_id[EAST]
                    cells[i].edge_exists[EAST] = True

                else:
                    sx = (1 + p.x()) * cell_size
                    sy = p.y() * cell_size
                    ex, ey = sx, sy + cell_size
                    edge = Edge(sx, sy, ex, ey, EAST)

                    edge.id_ = len(edges)
                    edges.append(edge)

                    cells[i].edge_id[EAST] = edge.id_
                    cells[i].edge_exists[EAST] = True

            if north not in selected:
                if cells[get_index(west)].edge_exists[NORTH]:
                    edges[cells[get_index(west)].edge_id[NORTH]].ex += cell_size
                    cells[i].edge_id[NORTH] = cells[get_index(west)].edge_id[NORTH]
                    cells[i].edge_exists[NORTH] = True

                else:
                    sx = p.x() * cell_size
                    sy = p.y() * cell_size
                    ex, ey = sx + cell_size, sy
                    edge = Edge(sx, sy, ex, ey, NORTH)

                    edge.id_ = len(edges)
                    edges.append(edge)

                    cells[i].edge_id[NORTH] = edge.id_
                    cells[i].edge_exists[NORTH] = True

            if south not in selected:
                if cells[get_index(west)].edge_exists[SOUTH]:
                    edges[cells[get_index(west)].edge_id[SOUTH]].ex += cell_size
                    cells[i].edge_id[SOUTH] = cells[get_index(west)].edge_id[SOUTH]
                    cells[i].edge_exists[SOUTH] = True

                else:
                    sx = p.x() * cell_size
                    sy = (1 + p.y()) * cell_size
                    ex, ey = sx + cell_size, sy
                    edge = Edge(sx, sy, ex, ey, SOUTH)

                    edge.id_ = len(edges)
                    edges.append(edge)

                    cells[i].edge_id[SOUTH] = edge.id_
                    cells[i].edge_exists[SOUTH] = True

    return edges


def get_index(p: QPoint) -> int:
    return p.y() * 9 + p.x()


def get_point(index: int) -> QPoint:
    return QPoint(index % 9, index // 9)


def valid(p: QPoint) -> bool:
    return 0 <= p.y() * 9 + p.x() <= 81


"""
void ConvertTileMapToPolyMap(int sx, int sy, int w, int h, float fBlockWidth, int pitch)
	{
		// Clear "PolyMap"
		vecEdges.clear();

		for (int x = 0; x < w; x++)
			for (int y = 0; y < h; y++)
				for (int j = 0; j < 4; j++)
				{
					world[(y + sy) * pitch + (x + sx)].edge_exist[j] = false;
					world[(y + sy) * pitch + (x + sx)].edge_id[j] = 0;
				}

		// Iterate through region from top left to bottom right
		for (int x = 1; x < w - 1; x++)
			for (int y = 1; y < h - 1; y++)
			{
				// Create some convenient indices
				int i = (y + sy) * pitch + (x + sx);			// This
				int n = (y + sy - 1) * pitch + (x + sx);		// Northern Neighbour
				int s = (y + sy + 1) * pitch + (x + sx);		// Southern Neighbour
				int w = (y + sy) * pitch + (x + sx - 1);	// Western Neighbour
				int e = (y + sy) * pitch + (x + sx + 1);	// Eastern Neighbour

				// If this cell exists, check if it needs edges
				if (world[i].exist)
				{
					// If this cell has no western neighbour, it needs a western edge
					if (!world[w].exist)
					{
						// It can either extend it from its northern neighbour if they have
						// one, or It can start a new one.
						if (world[n].edge_exist[WEST])
						{
							// Northern neighbour has a western edge, so grow it downwards
							vecEdges[world[n].edge_id[WEST]].ey += fBlockWidth;
							world[i].edge_id[WEST] = world[n].edge_id[WEST];
							world[i].edge_exist[WEST] = true;
						}
						else
						{
							// Northern neighbour does not have one, so create one
							sEdge edge;
							edge.sx = (sx + x) * fBlockWidth; edge.sy = (sy + y) * fBlockWidth;
							edge.ex = edge.sx; edge.ey = edge.sy + fBlockWidth;

							// Add edge to Polygon Pool
							int edge_id = vecEdges.size();
							vecEdges.push_back(edge);

							// Update tile information with edge information
							world[i].edge_id[WEST] = edge_id;
							world[i].edge_exist[WEST] = true;
						}
					}

					// If this cell dont have an eastern neignbour, It needs a eastern edge
					if (!world[e].exist)
					{
						// It can either extend it from its northern neighbour if they have
						// one, or It can start a new one.
						if (world[n].edge_exist[EAST])
						{
							// Northern neighbour has one, so grow it downwards
							vecEdges[world[n].edge_id[EAST]].ey += fBlockWidth;
							world[i].edge_id[EAST] = world[n].edge_id[EAST];
							world[i].edge_exist[EAST] = true;
						}
						else
						{
							// Northern neighbour does not have one, so create one
							sEdge edge;
							edge.sx = (sx + x + 1) * fBlockWidth; edge.sy = (sy + y) * fBlockWidth;
							edge.ex = edge.sx; edge.ey = edge.sy + fBlockWidth;

							// Add edge to Polygon Pool
							int edge_id = vecEdges.size();
							vecEdges.push_back(edge);

							// Update tile information with edge information
							world[i].edge_id[EAST] = edge_id;
							world[i].edge_exist[EAST] = true;
						}
					}

					// If this cell doesnt have a northern neignbour, It needs a northern edge
					if (!world[n].exist)
					{
						// It can either extend it from its western neighbour if they have
						// one, or It can start a new one.
						if (world[w].edge_exist[NORTH])
						{
							// Western neighbour has one, so grow it eastwards
							vecEdges[world[w].edge_id[NORTH]].ex += fBlockWidth;
							world[i].edge_id[NORTH] = world[w].edge_id[NORTH];
							world[i].edge_exist[NORTH] = true;
						}
						else
						{
							// Western neighbour does not have one, so create one
							sEdge edge;
							edge.sx = (sx + x) * fBlockWidth; edge.sy = (sy + y) * fBlockWidth;
							edge.ex = edge.sx + fBlockWidth; edge.ey = edge.sy;

							// Add edge to Polygon Pool
							int edge_id = vecEdges.size();
							vecEdges.push_back(edge);

							// Update tile information with edge information
							world[i].edge_id[NORTH] = edge_id;
							world[i].edge_exist[NORTH] = true;
						}
					}

					// If this cell doesnt have a southern neignbour, It needs a southern edge
					if (!world[s].exist)
					{
						// It can either extend it from its western neighbour if they have
						// one, or It can start a new one.
						if (world[w].edge_exist[SOUTH])
						{
							// Western neighbour has one, so grow it eastwards
							vecEdges[world[w].edge_id[SOUTH]].ex += fBlockWidth;
							world[i].edge_id[SOUTH] = world[w].edge_id[SOUTH];
							world[i].edge_exist[SOUTH] = true;
						}
						else
						{
							// Western neighbour does not have one, so I need to create one
							sEdge edge;
							edge.sx = (sx + x) * fBlockWidth; edge.sy = (sy + y + 1) * fBlockWidth;
							edge.ex = edge.sx + fBlockWidth; edge.ey = edge.sy;

							// Add edge to Polygon Pool
							int edge_id = vecEdges.size();
							vecEdges.push_back(edge);

							// Update tile information with edge information
							world[i].edge_id[SOUTH] = edge_id;
							world[i].edge_exist[SOUTH] = true;
						}
					}

				}

			}
	}
"""
