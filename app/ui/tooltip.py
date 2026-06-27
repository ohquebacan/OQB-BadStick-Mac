import tkinter as tk


class ToolTip:
    def __init__(self, widget, text: str, color: str = "#cc0000"):
        self.widget = widget
        self.text = text
        self.color = color
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text,
            background=self.color,
            foreground="white",
            relief="solid",
            borderwidth=1,
            font=("Helvetica", 11),
            wraplength=280,
            justify="left",
            padx=8, pady=6,
        ).pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
