class TrafficManager:
    def __init__(self, nav_graph):
        self.nav_graph = nav_graph
    
    def check_collision(self, robot_positions):
        occupied_positions = set()
        for pos in robot_positions:
            if pos in occupied_positions:
                return True  # Collision detected
            occupied_positions.add(pos)
        return False
    