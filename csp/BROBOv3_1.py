from asyncio.windows_events import NULL
import tkinter as tk
from tkinter import messagebox
from stock_cutter_1d import solveCut
from alns_stock_cutter import alnsSolver
#from ortools.sat.python import cp_model

class CutOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cut Optimizer")

        self.stock_length = tk.StringVar()
        self.blade_width = tk.StringVar()
        self.dead_zone = tk.StringVar()

        self.cut_lengths = []
        self.cut_quantities = []

        self.create_widgets()

    def create_widgets(self):
        self.root.geometry("270x400")  # Set the initial window size

        tk.Label(self.root, text="Stock Length:").pack()
        tk.Entry(self.root, textvariable=self.stock_length).pack()

        tk.Label(self.root, text="Blade Width:").pack()
        tk.Entry(self.root, textvariable=self.blade_width).pack()

        tk.Label(self.root, text="Dead Zone:").pack()
        tk.Entry(self.root, textvariable=self.dead_zone).pack()

        self.add_cut_button = tk.Button(self.root, text="Add Cut", command=self.add_cut)
        self.add_cut_button.pack()
        self.add_cut_button.config(state="disabled")  # Disable the button initially

        self.optimize_button = tk.Button(self.root, text="Optimize Cuts", command=self.optimize_cuts)
        self.optimize_button.pack()

        self.cut_canvas = tk.Canvas(self.root)
        self.cut_frame = tk.Frame(self.cut_canvas)

        self.cut_scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.cut_canvas.yview)
        self.cut_canvas.configure(yscrollcommand=self.cut_scrollbar.set)

        self.cut_scrollbar.pack(side="right", fill="y")
        self.cut_canvas.pack(side="left", fill="both", expand=True)
        self.cut_canvas.create_window((0, 0), window=self.cut_frame, anchor="nw")

        self.cut_frame.bind("<Configure>", self.on_frame_configure)

        tk.Label(self.cut_frame, text="Cut Length").grid(row=0, column=0)
        tk.Label(self.cut_frame, text="Quantity").grid(row=0, column=1)

        # Bind a function to be called whenever the entry fields are updated
        self.stock_length.trace_add("write", self.check_initial_params)
        self.blade_width.trace_add("write", self.check_initial_params)
        self.dead_zone.trace_add("write", self.check_initial_params)

    def on_frame_configure(self, event):
        self.cut_canvas.configure(scrollregion=self.cut_canvas.bbox("all"))

    def check_initial_params(self, *args):
        # Check if all three initial parameters are provided
        if self.stock_length.get() and self.blade_width.get() and self.dead_zone.get():
            self.add_cut_button.config(state="normal")  # Enable the button
        else:
            self.add_cut_button.config(state="disabled")  # Disable the button

    def add_cut(self):
        cut_length = tk.StringVar()
        cut_quantity = tk.StringVar()

        entry_cut_length = tk.Entry(self.cut_frame, textvariable=cut_length)
        entry_cut_quantity = tk.Entry(self.cut_frame, textvariable=cut_quantity)

        entry_cut_length.grid(row=len(self.cut_lengths) + 1, column=0)
        entry_cut_quantity.grid(row=len(self.cut_quantities) + 1, column=1)

        self.cut_lengths.append(cut_length)
        self.cut_quantities.append(cut_quantity)


    def scaleMeasurement(self, measurement, scaleFactor):
        return int(float(measurement) * scaleFactor)

    def zipCutData(self, cut_lengths, cut_quantities):
        return sorted(zip(cut_lengths, cut_quantities), key=lambda pair: pair[0], reverse=True)

    def flattenCutData(self, cutData):   
        return [length for (length, quantity) in cutData for _ in range(quantity)]
    
    def addBladeKerf(self, cut_lengths, bladeKerf):
        return [length + bladeKerf for length in cut_lengths]
    
    def optimize_cuts(self):
        try:
            searchType = "OR-Tools"
            scale_factor = 1000
            stock_length = self.scaleMeasurement(self.stock_length.get(), scale_factor)
            blade_width = self.scaleMeasurement(self.blade_width.get(), scale_factor)
            dead_zone = self.scaleMeasurement(self.dead_zone.get(), scale_factor)
            working_length = stock_length - dead_zone
            cut_quantities = [int(cut_quantity.get()) for cut_quantity in self.cut_quantities]
            sorted_pairs = sorted(zip(cut_lengths, cut_quantities), key=lambda pair: pair[0], reverse=True)

            # Call the new solver here
            consumed_big_rolls = solveCut(sorted_pairs, working_length, blade_width, output_json=False, large_model=True, greedy_model=False)

            # Display the results or perform any further actions
            for idx, stick in enumerate(consumed_big_rolls):
                adjusted_lengths = [float(length - blade_width) / scale_factor for length in stick[1]]
                print(f"Stick {idx + 1}: {adjusted_lengths}")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CutOptimizerApp(root)
    root.mainloop()
