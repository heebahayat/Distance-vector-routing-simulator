import tkinter as tk
from tkinter import ttk, messagebox
import math

INF = float('inf')

class RouterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Distance Vector Routing Simulator")
        self.root.geometry("1100x700")

        # Network State
        self.nodes = {'A': (150, 200), 'B': (350, 100), 'C': (550, 200), 'D': (350, 350)}
        self.links = [('A', 'B', 2), ('B', 'C', 3), ('A', 'D', 7), ('C', 'D', 1)]
        self.routing_tables = {}
        self.poison_reverse = tk.BooleanVar(value=True)

        self.setup_ui()
        self.initialize_tables()
        self.draw_network()

    def setup_ui(self):
        # Control Panel
        control_frame = ttk.LabelFrame(self.root, text="Controls", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Button(control_frame, text="Step Iteration", command=self.step_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Run to Convergence", command=self.converge_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(control_frame, text="Split Horizon w/ Poison Reverse", variable=self.poison_reverse).pack(side=tk.LEFT, padx=15)

        # Main Layout
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Canvas for Graph Visuals
        self.canvas = tk.Canvas(main_pane, bg="#1e1e2e", highlightthickness=0)
        main_pane.add(self.canvas, weight=2)

        # Side Panel for Routing Tables
        table_frame = ttk.LabelFrame(main_pane, text="Live Routing Tables", padding=10)
        main_pane.add(table_frame, weight=1)

        self.table_text = tk.Text(table_frame, wrap=tk.NONE, font=("Consolas", 10), bg="#181825", fg="#cdd6f4")
        self.table_text.pack(fill=tk.BOTH, expand=True)

    def draw_network(self):
        self.canvas.delete("all")

        # Draw Links
        for u, v, cost in self.links:
            x1, y1 = self.nodes[u]
            x2, y2 = self.nodes[v]
            self.canvas.create_line(x1, y1, x2, y2, fill="#a6adc8", width=3)

            # Link Cost Badge
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            self.canvas.create_rectangle(mx-15, my-12, mx+15, my+12, fill="#313244", outline="#89b4fa")
            self.canvas.create_text(mx, my, text=str(cost), fill="#f5e0dc", font=("Arial", 10, "bold"))

        # Draw Router Nodes
        for name, (x, y) in self.nodes.items():
            self.canvas.create_oval(x-25, y-25, x+25, y+25, fill="#89b4fa", outline="#b4befe", width=2)
            self.canvas.create_text(x, y, text=name, fill="#11111b", font=("Arial", 12, "bold"))

    def initialize_tables(self):
        all_nodes = list(self.nodes.keys())
        for n in all_nodes:
            self.routing_tables[n] = {dest: (n, 0) if dest == n else (None, INF) for dest in all_nodes}

        # Set Direct Neighbors
        for u, v, cost in self.links:
            self.routing_tables[u][v] = (v, cost)
            self.routing_tables[v][u] = (u, cost)

        self.update_table_display()

    def step_simulation(self):
        all_nodes = list(self.nodes.keys())
        new_tables = {n: self.routing_tables[n].copy() for n in all_nodes}

        for u in all_nodes:
            for v in all_nodes:
                if u == v: continue
                # Apply Bellman-Ford across neighbors
                for neighbor, (nh, cost_to_n) in self.routing_tables[u].items():
                    if cost_to_n == INF or neighbor == u: continue
                    
                    # Received distance vector entry
                    reported_cost = self.routing_tables[neighbor][v][1]
                    
                    # Poison Reverse Check
                    if self.poison_reverse.get() and self.routing_tables[neighbor][v][0] == u:
                        reported_cost = INF

                    total = cost_to_n + reported_cost
                    if total < new_tables[u][v][1]:
                        new_tables[u][v] = (neighbor, total)

        self.routing_tables = new_tables
        self.update_table_display()

    def converge_simulation(self):
        for _ in range(10):
            self.step_simulation()

    def update_table_display(self):
        self.table_text.delete("1.0", tk.END)
        for router, table in sorted(self.routing_tables.items()):
            self.table_text.insert(tk.END, f"=== Router {router} ===\n")
            self.table_text.insert(tk.END, f"{'Dest':<6} | {'Next':<6} | {'Cost':<5}\n")
            self.table_text.insert(tk.END, "-" * 23 + "\n")
            for dest, (next_hop, cost) in sorted(table.items()):
                c_str = "INF" if cost == INF else str(cost)
                nh_str = str(next_hop) if next_hop else "-"
                self.table_text.insert(tk.END, f"{dest:<6} | {nh_str:<6} | {c_str:<5}\n")
            self.table_text.insert(tk.END, "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = RouterGUI(root)
    root.mainloop()