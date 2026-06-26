import customtkinter as ctk


class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1E1E1E", corner_radius=8, **kwargs)
        self._build()

    def _build(self):
        # Progress bar row
        bar_row = ctk.CTkFrame(self, fg_color="transparent")
        bar_row.pack(fill="x", padx=14, pady=(12, 4))

        self._bar = ctk.CTkProgressBar(
            bar_row,
            fg_color="#2d2d2d",
            progress_color="#107C10",
        )
        self._bar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._bar.set(0)

        self._pct_label = ctk.CTkLabel(
            bar_row,
            text="0%",
            font=ctk.CTkFont(size=12),
            width=36,
            anchor="e",
        )
        self._pct_label.pack(side="left")

        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="#666666",
            anchor="w",
        )
        self._status_label.pack(fill="x", padx=14, pady=(0, 4))

        self._log = ctk.CTkTextbox(
            self,
            height=130,
            fg_color="#0d0d0d",
            font=ctk.CTkFont(family="Courier", size=11),
            state="disabled",
            wrap="word",
        )
        self._log.pack(fill="x", padx=14, pady=(0, 12))

    def set_progress(self, value: float, status: str = ""):
        value = max(0.0, min(1.0, value))
        self._bar.set(value)
        self._pct_label.configure(text=f"{int(value * 100)}%")
        if status:
            self._status_label.configure(text=status)

    def log(self, message: str):
        self._log.configure(state="normal")
        self._log.insert("end", f"> {message}\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
