class FleetManager:
    def __init__(self):
        self.robots = []
    
    def add_robot(self, robot):
        self.robots.append(robot)
    
    def assign_task(self, robot_id, destination):
        for robot in self.robots:
            if robot.id == robot_id:
                robot.destination = destination
                robot.status = "Moving"