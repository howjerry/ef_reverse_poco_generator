import tkinter as tk
from reverse_poco_generator_gui import ReversePocoGeneratorGUI

def main():
    root = tk.Tk()
    app = ReversePocoGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()