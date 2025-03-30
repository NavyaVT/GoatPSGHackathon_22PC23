import tkinter as tk
from tkinter import messagebox
import math
import logging
import datetime
from src.models.robot import Robot
from src.models.nav_graph import NavGraph

class NavGraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management System")
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()
        self.nav_graph = NavGraph()
        self.robot_objects = {}
        self.selected_robot = None
        self.destination_lane = None
        self.destination_position = None
        self.robot_radius = 10
        self.robot_positions = {0: (1, 0)}
        self.robot_labels = {}

        logging.basicConfig(filename=r'handling/logs/fleet_logs.txt', level=logging.INFO,
                            format='%(message)s',
                            filemode='a')

        self.add_robot_to_canvas(0)

        if not self.nav_graph.lanes:
            self.display_error_message()
        else:
            self.translate_and_scale_graph()
            self.draw_graph()
            self.setup_event_handlers()

    def add_robot_to_canvas(self, robot_id):
        lane_id, position = self.robot_positions[robot_id]
        try:
            x, y = self.nav_graph.get_lane_coords(lane_id, position)
            robot = self.canvas.create_oval(x - self.robot_radius, y - self.robot_radius,
                                            x + self.robot_radius, y + self.robot_radius,
                                            fill="red", tags=f"robot_{robot_id}")
            self.robot_objects[robot_id] = Robot(robot_id, None, robot)
            label = self.robot_labels.get(robot_id, self.robot_objects[robot_id].name)
            self.canvas.create_text(x, y - 15, text=label, tags=f"robot_label_{robot_id}", font=("Arial", 10, "bold"))
        except (KeyError, IndexError) as e:
            logging.error(f"Error in add_robot_to_canvas: {e}")

    def redraw_canvas(self):
        self.canvas.delete("all")
        self.draw_graph()
        for robot_id, (lane_id, position) in self.robot_positions.items():
            try:
                x, y = self.nav_graph.get_lane_coords(lane_id, position)
                if robot_id in self.robot_objects:
                    self.canvas.coords(self.robot_objects[robot_id].canvas_object,
                                       x - self.robot_radius, y - self.robot_radius,
                                       x + self.robot_radius, y + self.robot_radius)
                    self.canvas.coords(f"robot_label_{robot_id}", x, y - 15)
                else:
                    self.add_robot_to_canvas(robot_id)
            except (KeyError, IndexError) as e:
                logging.error(f"Error in redraw_canvas: {e}")
                continue

    def translate_and_scale_graph(self):
        x_coords = [coord[0] for coord in self.nav_graph.vertex_coords.values()]
        y_coords = [coord[1] for coord in self.nav_graph.vertex_coords.values()]
        min_x = min(x_coords)
        min_y = min(y_coords)
        max_x = max(x_coords)
        max_y = max(y_coords)
        width = max_x - min_x
        height = max_y - min_y
        scale = min(700 / width, 500 / height) if width > 0 and height > 0 else 40
        for i, coord in self.nav_graph.vertex_coords.items():
            x, y = coord
            self.nav_graph.vertex_coords[i] = ((x - min_x) * scale + 50, (y - min_y) * scale + 50)

    def display_error_message(self):
        self.canvas.create_text(400, 300, text="Error: Invalid or empty graph data.", fill="red", font=("Arial", 16))
        logging.error("Invalid or empty graph data.")

    def draw_graph(self):
        for i, lane in enumerate(self.nav_graph.lanes):
            start, end, _ = lane
            x1, y1 = self.nav_graph.vertex_coords[str(start)]
            x2, y2 = self.nav_graph.vertex_coords[str(end)]
            self.canvas.create_line(x1, y1, x2, y2, fill="gray", tags=f"lane_{i}")
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_text(mid_x, mid_y, text=f"L{i}", tags=f"lane_label_{i}")

    def setup_event_handlers(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        logging.info(f"Clicked at ({x}, {y})")
        lane_clicked = None
        lane_position = None
        for i, lane in enumerate(self.nav_graph.lanes):
            x1, y1 = self.nav_graph.vertex_coords[str(lane[0])]
            x2, y2 = self.nav_graph.vertex_coords[str(lane[1])]
            distance = self.point_line_distance(x, y, x1, y1, x2, y2)
            if distance <= 5:
                lane_clicked = i
                lane_position = self.calculate_lane_position(x, y, x1, y1, x2, y2)
                logging.info(f"Lane clicked: {lane_clicked}, position: {lane_position}")
                break

        if lane_clicked is not None:
            if self.selected_robot is None:
                robot_at_lane = None
                for robot_id, (robot_lane, _) in self.robot_positions.items():
                    if robot_lane == lane_clicked:
                        robot_at_lane = robot_id
                        break
                if robot_at_lane is not None:
                    self.selected_robot = robot_at_lane
                    logging.info(f"Robot {robot_at_lane} is on lane {lane_clicked}")
            else:
                self.move_robot_to_lane_point(self.selected_robot, lane_clicked, lane_position)

    def point_line_distance(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx ** 2 + dy ** 2)
        t = max(0, min(1, t))
        lx = x1 + t * dx
        ly = y1 + t * dy
        return math.sqrt((px - lx) ** 2 + (py - ly) ** 2)

    def calculate_lane_position(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return 0.5
        t = ((px - x1) * dx + (py - y1) * dy) / (dx ** 2 + dy ** 2)
        return max(0, min(1, t))

    def move_robot_to_lane_point(self, robot_id, lane_id, position):
        if robot_id in self.robot_objects:
            self.animate_robot_movement_to_lane_point(robot_id, lane_id, position)
            self.selected_robot = None
        else:
            print(f"Error: Robot with ID {robot_id} not found.")

    def animate_robot_movement_to_lane_point(self, robot_id, lane_id, position, callback=None, callback_index=None):
        def move_step(current_position, target_position, step):
            if step <= 50:
                try:
                    x, y = self.nav_graph.get_lane_coords(lane_id, target_position)
                    self.canvas.coords(self.robot_objects[robot_id].canvas_object,
                                       x - self.robot_radius, y - self.robot_radius,
                                       x + self.robot_radius, y + self.robot_radius)
                    self.canvas.coords(f"robot_label_{robot_id}", x, y - 15)
                    self.robot_positions[robot_id] = (lane_id, target_position)
                    self.root.update()
                    self.root.after(20, move_step, current_position, target_position, step + 1)
                except (KeyError, IndexError) as e:
                    logging.error(f"Error in move_step: {e}")
                    return
            else:
                try:
                    self.robot_positions[robot_id] = (lane_id, target_position)
                    self.redraw_canvas()
                    if callback:
                        callback(callback_index + 1, 0)
                except (KeyError, IndexError) as e:
                    logging.error(f"Error in move_step (final): {e}")

        current_lane, current_position = self.robot_positions[robot_id]
        before_coords = self.nav_graph.get_lane_coords(robot_id, current_position)
        move_step(current_position, position, 0)
        after_coords = self.nav_graph.get_lane_coords(robot_id, position)
        lane_name = f"Lane {lane_id}" if lane_id is not None else "Vertex"
        self.log_movement(robot_id, before_coords, after_coords, lane_name)

    def log_movement(self, robot_id, before_coords, after_coords, lane_name):
        robot_name = f"Robot {robot_id}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        before_coords_str = f"({before_coords[0]}, {before_coords[1]})"
        after_coords_str = f"({after_coords[0]}, {after_coords[1]})"
        log_entry = f"{robot_name} {timestamp} {before_coords_str} {after_coords_str} {lane_name}"
        logging.info(log_entry)
        logging.getLogger().handlers[0].flush()