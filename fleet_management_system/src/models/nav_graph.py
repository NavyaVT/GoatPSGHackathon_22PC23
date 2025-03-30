import json

class NavGraph:
    def __init__(self, filename=r'data\nav_graph_3.json'):
        self.lanes = []
        self.vertex_coords = {}
        self.data = {}
        self.load_data(filename)

    def load_data(self, filename):
        try:
            with open(filename, 'r') as f:
                self.data = json.load(f)
                self.lanes = self.data.get("lanes", [])
                self.vertex_coords = self.data.get("vertex_coords", {})
        except FileNotFoundError:
            print(f"Error: {filename} not found.")

    def get_lane_coords(self, lane_id, position):
        start, end, _ = self.lanes[lane_id]
        x1, y1 = self.vertex_coords[str(start)]  # vertex_coords keys are strings
        x2, y2 = self.vertex_coords[str(end)]
        x = x1 + (x2 - x1) * position
        y = y1 + (y2 - y1) * position
        return x, y

    def get_lane_by_vertices(self, start_vertex, end_vertex):
        for i, (start, end, _) in enumerate(self.lanes):
            if (start == start_vertex and end == end_vertex) or (start == end_vertex and end == start_vertex):
                return i
        return None
