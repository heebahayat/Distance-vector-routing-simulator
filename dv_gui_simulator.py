import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import time

INF = float('inf')

class DistanceVectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Distance Vector Routing Simulator")
        self.root.geometry("1200x750")
        self.root.configure(bg="#11111b")

        #Network State
        self.nodes = {
            'A': [180, 220],
            'B': [420, 120],
            'C': [660, 220],
            'D': [420, 420]
        }
        self.links = [
            ('A', 'B', 2),
            ('B', 'C', 3),
            ('A', 'D', 7),
            ('C', 'D', 1)
        ]
        self.routing_tables = {}
        self.poison_reverse = tk.BooleanVar(value=True)

        # Dragging state
        self.drag_node = None
        self.offset_x = 0
        self.offset_y = 0

        self.setup_styles()
        self.setup_ui()
        self.initialize_tables()
        self.draw_network()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TFrame', background='#181825')
        style.configure('TLabelframe', background='#181825', foreground='#cdd6f4', bordercolor='#313244')
        style.configure('TLabelframe.Label', background='#181825', foreground='#89b4fa', font=('Segoe UI', 10, 'bold'))
        style.configure('TButton', font=('Segoe UI', 9, 'bold'), background='#313244', foreground='#cdd6f4', borderwidth=0)
        style.map('TButton', background=[('active', '#45475a')], foreground=[('active', '#ffffff')])
        style.configure('TCheckbutton', background='#181825', foreground='#cdd6f4', font=('Segoe UI', 9))

    def setup_ui(self):
        # Top Header Bar
        header = tk.Frame(self.root, bg="#1e1e2e", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        title_label = tk.Label(header, text="DISTANCE VECTOR ROUTING SIMULATOR", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Control Toolbar
        toolbar = ttk.LabelFrame(self.root, text=" Network Controls ", padding=10)
        toolbar.pack(fill=tk.X, padx=15, pady=10)

        btn_step = tk.Button(toolbar, text="▶ Step Iteration", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", command=self.step_simulation, padx=10, pady=4)
        btn_step.pack(side=tk.LEFT, padx=5)

        btn_converge = tk.Button(toolbar, text="⚡ Run to Convergence", bg="#89b4fa", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", command=self.converge_simulation, padx=10, pady=4)
        btn_converge.pack(side=tk.LEFT, padx=5)

        btn_add_node = tk.Button(toolbar, text="+ Add Router", bg="#313244", fg="#cdd6f4", font=("Segoe UI", 9), relief="flat", command=self.add_router, padx=8, pady=4)
        btn_add_node.pack(side=tk.LEFT, padx=5)

        btn_add_link = tk.Button(toolbar, text="🔗 Connect Link", bg="#313244", fg="#cdd6f4", font=("Segoe UI", 9), relief="flat", command=self.add_link, padx=8, pady=4)
        btn_add_link.pack(side=tk.LEFT, padx=5)

        btn_del_link = tk.Button(toolbar, text="✂ Remove Link", bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), relief="flat", command=self.remove_link, padx=8, pady=4)
        btn_del_link.pack(side=tk.LEFT, padx=5)

        chk_poison = ttk.Checkbutton(toolbar, text="Split Horizon w/ Poison Reverse", variable=self.poison_reverse)
        chk_poison.pack(side=tk.RIGHT, padx=10)

        # Main Workspace
        workspace = tk.Frame(self.root, bg="#11111b")
        workspace.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Canvas Frame (Left Side)
        canvas_card = ttk.LabelFrame(workspace, text=" Topology View (Drag Routers to Move) ", padding=5)
        canvas_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(canvas_card, bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Canvas Drag Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Routing Tables Panel (Right Side)
        tables_card = ttk.LabelFrame(workspace, text=" Live Routing Tables ", padding=5)
        tables_card.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))
        tables_card.config(width=340)

        self.table_text = tk.Text(tables_card, wrap=tk.NONE, font=("Cascadia Code", 9), bg="#181825", fg="#cdd6f4", relief="flat", width=40)
        self.table_text.pack(fill=tk.BOTH, expand=True)

    def draw_network(self):
        self.canvas.delete("all")

        # Draw Grid background lines for modern aesthetic
        for x in range(0, 800, 40):
            self.canvas.create_line(x, 0, x, 600, fill="#181825", width=1)
        for y in range(0, 600, 40):
            self.canvas.create_line(0, y, 800, y, fill="#181825", width=1)

        # Draw Links
        for u, v, cost in self.links:
            if u in self.nodes and v in self.nodes:
                x1, y1 = self.nodes[u]
                x2, y2 = self.nodes[v]
                self.canvas.create_line(x1, y1, x2, y2, fill="#45475a", width=4)

                # Midpoint Cost Badge
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_oval(mx-14, my-14, mx+14, my+14, fill="#313244", outline="#89b4fa", width=2)
                self.canvas.create_text(mx, my, text=str(cost), fill="#f5e0dc", font=("Segoe UI", 9, "bold"))

        # Draw Routers (Nodes)
        for name, (x, y) in self.nodes.items():
            # Glow Effect
            self.canvas.create_oval(x-28, y-28, x+28, y+28, fill="", outline="#89b4fa", width=1)
            # Core Node Circle
            self.canvas.create_oval(x-22, y-22, x+22, y+22, fill="#89b4fa", outline="#b4befe", width=2, tags=("node", name))
            self.canvas.create_text(x, y, text=name, fill="#11111b", font=("Segoe UI", 11, "bold"), tags=("node", name))

    def animate_packets(self):
        """Animates packet exchanges along connected links."""
        packets = []
        for u, v, _ in self.links:
            if u in self.nodes and v in self.nodes:
                x1, y1 = self.nodes[u]
                x2, y2 = self.nodes[v]
                p1 = self.canvas.create_oval(x1-5, y1-5, x1+5, y1+5, fill="#a6e3a1", outline="")
                p2 = self.canvas.create_oval(x2-5, y2-5, x2+5, y2+5, fill="#a6e3a1", outline="")
                packets.append((p1, x1, y1, x2, y2))
                packets.append((p2, x2, y2, x1, y1))

        steps = 15
        for s in range(steps + 1):
            t = s / steps
            for p, x1, y1, x2, y2 in packets:
                cx = x1 + (x2 - x1) * t
                cy = y1 + (y2 - y1) * t
                self.canvas.coords(p, cx-5, cy-5, cx+5, cy+5)
            self.root.update()
            time.sleep(0.015)

        for p, _, _, _, _ in packets:
            self.canvas.delete(p)

    def initialize_tables(self):
        all_nodes = sorted(list(self.nodes.keys()))
        self.routing_tables = {}
        for n in all_nodes:
            self.routing_tables[n] = {dest: (n, 0) if dest == n else (None, INF) for dest in all_nodes}

        for u, v, cost in self.links:
            if u in self.nodes and v in self.nodes:
                self.routing_tables[u][v] = (v, cost)
                self.routing_tables[v][u] = (u, cost)

        self.update_table_display()

    def step_simulation(self):
        self.animate_packets()

        all_nodes = sorted(list(self.nodes.keys()))
        new_tables = {n: self.routing_tables[n].copy() for n in all_nodes}

        for u in all_nodes:
            for v in all_nodes:
                if u == v: continue
                for neighbor in all_nodes:
                    # Check if direct neighbor
                    cost_to_neighbor = INF
                    for lu, lv, lcost in self.links:
                        if (lu == u and lv == neighbor) or (lv == u and lu == neighbor):
                            cost_to_neighbor = lcost
                            break

                    if cost_to_neighbor == INF: continue

                    reported_cost = self.routing_tables[neighbor].get(v, (None, INF))[1]

                    # Poison Reverse Check
                    if self.poison_reverse.get():
                        next_hop_of_neighbor = self.routing_tables[neighbor].get(v, (None, INF))[0]
                        if next_hop_of_neighbor == u:
                            reported_cost = INF

                    total = cost_to_neighbor + reported_cost
                    if total < new_tables[u][v][1]:
                        new_tables[u][v] = (neighbor, total)

        self.routing_tables = new_tables
        self.update_table_display()

    def converge_simulation(self):
        for _ in range(8):
            self.step_simulation()

    def update_table_display(self):
        self.table_text.delete("1.0", tk.END)
        for router in sorted(self.routing_tables.keys()):
            table = self.routing_tables[router]
            self.table_text.insert(tk.END, f"  ROUTER {router}\n", "header")
            self.table_text.insert(tk.END, f"  {'Dest':<6} | {'Next':<6} | {'Cost':<5}\n")
            self.table_text.insert(tk.END, "  " + "-" * 23 + "\n")
            for dest in sorted(table.keys()):
                next_hop, cost = table[dest]
                c_str = "INF" if cost == INF else str(cost)
                nh_str = str(next_hop) if next_hop else "-"
                self.table_text.insert(tk.END, f"  {dest:<6} | {nh_str:<6} | {c_str:<5}\n")
            self.table_text.insert(tk.END, "\n")

    # Interactive Graph Controls
    def add_router(self):
        existing = set(self.nodes.keys())
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if char not in existing:
                self.nodes[char] = [300, 250]
                self.initialize_tables()
                self.draw_network()
                return
        messagebox.showinfo("Limit Reached", "Maximum router capacity reached.")

    def add_link(self):
        u = simpledialog.askstring("Source", "Enter Source Router Name (e.g., A):")
        if not u or u.upper() not in self.nodes: return
        v = simpledialog.askstring("Destination", "Enter Destination Router Name (e.g., B):")
        if not v or v.upper() not in self.nodes: return
        cost_str = simpledialog.askstring("Cost", "Enter Link Cost:")
        try:
            cost = int(cost_str)
            u, v = u.upper(), v.upper()
            self.links.append((u, v, cost))
            self.initialize_tables()
            self.draw_network()
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Input", "Cost must be a valid integer.")

    def remove_link(self):
        u = simpledialog.askstring("Source", "Enter Source Router Name to disconnect:")
        if not u or u.upper() not in self.nodes: return
        v = simpledialog.askstring("Destination", "Enter Destination Router Name:")
        if not v or v.upper() not in self.nodes: return
        u, v = u.upper(), v.upper()

        self.links = [l for l in self.links if not ((l[0] == u and l[1] == v) or (l[0] == v and l[1] == u))]
        self.initialize_tables()
        self.draw_network()

    # Canvas Drag Helpers
    def on_canvas_click(self, event):
        for name, (x, y) in self.nodes.items():
            if math.hypot(event.x - x, event.y - y) <= 25:
                self.drag_node = name
                self.offset_x = event.x - x
                self.offset_y = event.y - y
                break

    def on_canvas_drag(self, event):
        if self.drag_node:
            self.nodes[self.drag_node] = [event.x - self.offset_x, event.y - self.offset_y]
            self.draw_network()

    def on_canvas_release(self, event):
        self.drag_node = None

if __name__ == "__main__":
    root = tk.Tk()
    app = DistanceVectorGUI(root)
    root.mainloop()
