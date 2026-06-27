import customtkinter as ctk

from app.core.catalog import CATALOG

_KEYS = [k for k, v in CATALOG.items() if v["tab"] == "dashboards"]


class DashboardsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._vars = {k: ctk.BooleanVar(value=False) for k in _KEYS}
        self._toggleable   = []
        self._on_change_cb = None
        self._build()
        self.update_idletasks()

    def _build(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left preview ───────────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="#161616", corner_radius=0, width=230)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        self._prev_bg = ctk.CTkFrame(
            left, fg_color="#2a2a2a", corner_radius=10, width=200, height=160,
        )
        self._prev_bg.pack(pady=(24, 8), padx=14)
        self._prev_bg.pack_propagate(False)

        self._prev_title = ctk.CTkLabel(
            self._prev_bg, text="DASHBOARDS\n& LAUNCHERS",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#3a3a3a",
        )
        self._prev_title.place(relx=0.5, rely=0.4, anchor="center")

        self._prev_desc = ctk.CTkLabel(
            self._prev_bg, text="",
            font=ctk.CTkFont(size=9), text_color="#666666",
            wraplength=175, justify="center",
        )
        self._prev_desc.place(relx=0.5, rely=0.78, anchor="center")

        ctk.CTkLabel(
            left, text="Pasa el cursor sobre\nun dashboard para\nver detalles",
            font=ctk.CTkFont(size=10), text_color="#444444", justify="center",
        ).pack()

        # ── Right checkboxes ───────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            right, text="Dashboards / Launchers",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(16, 8))

        grid = ctk.CTkFrame(right, fg_color="transparent")
        grid.pack(fill="x", padx=14)
        grid.grid_columnconfigure((0, 1), weight=1)

        for i, key in enumerate(_KEYS):
            entry = CATALOG[key]
            row, col = divmod(i, 2)
            cb = ctk.CTkCheckBox(
                grid, text=entry["name"],
                variable=self._vars[key],
                command=self._on_change,
                fg_color="#107C10", hover_color="#0d6a0d",
            )
            cb.grid(row=row, column=col, sticky="w", padx=8, pady=5)
            cb.bind("<Enter>", lambda e, k=key: self._on_hover(k))
            cb.bind("<Leave>", lambda e: self._on_leave())
            self._toggleable.append(cb)

        ctk.CTkLabel(
            right, text="* XeXMenu 1.2 se instala por defecto con el exploit",
            font=ctk.CTkFont(size=10), text_color="#EF5350",
        ).pack(anchor="w", padx=14, pady=(14, 2))

        ctk.CTkLabel(
            right,
            text="Los seleccionados crean su carpeta en USB/Apps/ con instrucciones\n"
                 "de descarga manual dentro de un archivo LEER.txt.",
            font=ctk.CTkFont(size=10), text_color="#555555",
        ).pack(anchor="w", padx=14, pady=(0, 8))

    def _on_hover(self, key: str):
        entry = CATALOG[key]
        color = entry.get("color", "#2a4a2a")
        self._prev_bg.configure(fg_color=color)
        self._prev_title.configure(text=entry["name"], text_color="#eeeeee",
                                    font=ctk.CTkFont(size=14, weight="bold"))
        self._prev_desc.configure(text=entry["desc"], text_color="#bbbbbb")

    def _on_leave(self):
        self._prev_bg.configure(fg_color="#2a2a2a")
        self._prev_title.configure(text="DASHBOARDS\n& LAUNCHERS",
                                    text_color="#3a3a3a",
                                    font=ctk.CTkFont(size=13, weight="bold"))
        self._prev_desc.configure(text="")

    def _on_change(self):
        if self._on_change_cb:
            self._on_change_cb()

    def set_change_callback(self, cb):
        self._on_change_cb = cb

    def set_selections(self, opts: dict):
        for k, var in self._vars.items():
            if k in opts:
                var.set(opts[k])

    def get_options(self) -> dict:
        return {k: v.get() for k, v in self._vars.items()}

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in self._toggleable:
            w.configure(state=state)
