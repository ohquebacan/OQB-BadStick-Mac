import customtkinter as ctk

from app.core.catalog import CATALOG

# Free services first, then paid — explicit order
_FREE_KEYS = ["proto", "xblghost"]
_PAID_KEYS = ["xbls", "cipher", "xbguard", "xbnetwork", "nfinite", "tethered_live", "xbl_kyuubii"]
_KEYS = _FREE_KEYS + _PAID_KEYS


class StealthTab(ctk.CTkFrame):
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

        # ── Left logo panel ────────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="#161616", corner_radius=0, width=230)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        logo = ctk.CTkFrame(
            left, fg_color="#1a2a1a", corner_radius=10, width=200, height=160,
        )
        logo.pack(pady=(24, 8), padx=14)
        logo.pack_propagate(False)

        ctk.CTkLabel(
            logo, text="XBOX\nLIVE",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#107C10",
        ).place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(
            logo, text="STEALTH",
            font=ctk.CTkFont(size=11), text_color="#555555",
        ).place(relx=0.5, rely=0.72, anchor="center")

        ctk.CTkLabel(
            left, text="Stealth Servers",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#444444",
        ).pack(pady=(4, 0))

        ctk.CTkLabel(
            left, text="Protección contra\nbans en Xbox Live",
            font=ctk.CTkFont(size=10), text_color="#333333", justify="center",
        ).pack(pady=(2, 0))

        # ── Right panel ────────────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 4))

        ctk.CTkLabel(
            right, text="Stealth Networks",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(14, 8))

        # ── Recommendation box ─────────────────────────────────────────
        rec = ctk.CTkFrame(right, fg_color="#0d200d", corner_radius=8,
                           border_width=1, border_color="#107C10")
        rec.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(
            rec,
            text="⭐  Si es tu primera vez: usa Proto (gratis) o xblGhost (gratis)\n"
                 "Ambos funcionan con dashboard 17559 y son los más fáciles\n"
                 "de configurar para consolas con modificación por software.",
            font=ctk.CTkFont(size=10), text_color="#4CAF50",
            justify="left",
        ).pack(padx=12, pady=8, anchor="w")

        # ── Checkbox grid ──────────────────────────────────────────────
        grid = ctk.CTkFrame(right, fg_color="transparent")
        grid.pack(fill="x", padx=14)
        grid.grid_columnconfigure((0, 1), weight=1)

        for i, key in enumerate(_KEYS):
            entry  = CATALOG[key]
            is_free = entry.get("free", False)
            row, col = divmod(i, 2)

            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row, column=col, sticky="w", padx=4, pady=4)

            cb = ctk.CTkCheckBox(
                cell, text=entry["name"],
                variable=self._vars[key],
                command=self._on_change,
                fg_color="#107C10", hover_color="#0d6a0d",
            )
            cb.pack(side="left")
            self._toggleable.append(cb)

            badge_text  = "GRATIS"   if is_free else "De pago"
            badge_fg    = "#1a3a1a"  if is_free else "transparent"
            badge_color = "#4CAF50"  if is_free else "#555555"
            badge = ctk.CTkLabel(
                cell, text=badge_text,
                font=ctk.CTkFont(size=8, weight="bold"),
                fg_color=badge_fg, text_color=badge_color,
                corner_radius=4,
            )
            badge.pack(side="left", padx=(5, 0))

        # ── Yellow warning ─────────────────────────────────────────────
        warn = ctk.CTkFrame(right, fg_color="#2a2000", corner_radius=8,
                            border_width=1, border_color="#7a5f00")
        warn.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(
            warn,
            text="⚠  Ningún stealth server garantiza protección 100%.\n"
                 "Conectar a Xbox Live con consola modificada siempre\n"
                 "tiene riesgo de ban. Considera jugar offline.",
            font=ctk.CTkFont(size=10), text_color="#FFA726",
            justify="left",
        ).pack(padx=12, pady=8, anchor="w")

        ctk.CTkLabel(
            right,
            text="Cada servidor crea USB/Plugins/[nombre]/ con instrucciones en LEER.txt",
            font=ctk.CTkFont(size=9), text_color="#444444",
        ).pack(anchor="w", padx=14, pady=(6, 8))

    # ------------------------------------------------------------------ #

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
