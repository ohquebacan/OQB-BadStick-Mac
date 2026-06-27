import customtkinter as ctk

from app.core.catalog import CATALOG

_GROUPS = ["Plugins", "Personalización", "Retrocompatibilidad"]
_KEYS_BY_GROUP = {
    g: [k for k, v in CATALOG.items() if v["tab"] == "plugins" and v.get("group") == g]
    for g in _GROUPS
}


class PluginsTab(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        all_keys = [k for v in _KEYS_BY_GROUP.values() for k in v]
        self._vars = {k: ctk.BooleanVar(value=False) for k in all_keys}
        self._toggleable   = []
        self._on_change_cb = None
        self._build()
        self.update_idletasks()

    def _build(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Left preview panel ─────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="#161616", corner_radius=0, width=230)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        self._prev_bg = ctk.CTkFrame(
            left, fg_color="#2a2a2a", corner_radius=10, width=200, height=160,
        )
        self._prev_bg.pack(pady=(24, 8), padx=14)
        self._prev_bg.pack_propagate(False)

        self._prev_title = ctk.CTkLabel(
            self._prev_bg, text="PLUGINS\n& EXTRAS",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#3a3a3a",
        )
        self._prev_title.place(relx=0.5, rely=0.38, anchor="center")

        self._prev_group = ctk.CTkLabel(
            self._prev_bg, text="",
            font=ctk.CTkFont(size=9), text_color="#888888",
        )
        self._prev_group.place(relx=0.5, rely=0.65, anchor="center")

        self._prev_desc = ctk.CTkLabel(
            self._prev_bg, text="",
            font=ctk.CTkFont(size=9), text_color="#777777",
            wraplength=175, justify="center",
        )
        self._prev_desc.place(relx=0.5, rely=0.82, anchor="center")

        ctk.CTkLabel(
            left, text="Pasa el cursor sobre\nun plugin para ver\nsu descripción",
            font=ctk.CTkFont(size=10), text_color="#444444", justify="center",
        ).pack()

        ctk.CTkLabel(
            left, text="Todos crean carpetas\ncon instrucciones",
            font=ctk.CTkFont(size=9), text_color="#333333", justify="center",
        ).pack(pady=(4, 0))

        # ── Right panel — 3 column groups ─────────────────────────────
        right = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#3a3a3a",
        )
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        cols_frame = ctk.CTkFrame(right, fg_color="transparent")
        cols_frame.pack(fill="x", padx=8, pady=14)
        cols_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for col_idx, group in enumerate(_GROUPS):
            col = ctk.CTkFrame(cols_frame, fg_color="#1e1e1e", corner_radius=8)
            col.grid(row=0, column=col_idx, sticky="nsew", padx=4)

            ctk.CTkLabel(
                col, text=group,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#aaaaaa",
            ).pack(anchor="w", padx=12, pady=(10, 6))

            for key in _KEYS_BY_GROUP.get(group, []):
                entry = CATALOG[key]
                cb = ctk.CTkCheckBox(
                    col, text=entry["name"],
                    variable=self._vars[key],
                    command=self._on_change,
                    fg_color="#107C10", hover_color="#0d6a0d",
                    font=ctk.CTkFont(size=11),
                )
                cb.pack(anchor="w", padx=12, pady=2)
                cb.bind("<Enter>", lambda e, k=key, g=group: self._on_hover(k, g))
                cb.bind("<Leave>", lambda e: self._on_leave())
                self._toggleable.append(cb)

            ctk.CTkFrame(col, height=8, fg_color="transparent").pack()

    # ------------------------------------------------------------------ #

    def _on_hover(self, key: str, group: str):
        entry = CATALOG[key]
        self._prev_bg.configure(fg_color="#1e2a3a")
        self._prev_title.configure(text=entry["name"], text_color="#eeeeee",
                                   font=ctk.CTkFont(size=13, weight="bold"))
        self._prev_group.configure(text=group, text_color="#888888")
        self._prev_desc.configure(text=entry.get("desc", ""), text_color="#bbbbbb")

    def _on_leave(self):
        self._prev_bg.configure(fg_color="#2a2a2a")
        self._prev_title.configure(text="PLUGINS\n& EXTRAS", text_color="#3a3a3a",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        self._prev_group.configure(text="")
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
