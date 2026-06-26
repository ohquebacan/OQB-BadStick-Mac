import customtkinter as ctk


class OptionsFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kwargs)
        self.payload_var = ctk.StringVar(value="xeunshackle")
        self.nand_var = ctk.BooleanVar(value=True)
        self._toggleable: list = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Exploit ──────────────────────────────────────────
        exploit_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)
        exploit_frame.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="nsew")

        ctk.CTkLabel(
            exploit_frame,
            text="Exploit",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        # ABadAvatar is the only option — disabled radio to show it's fixed
        self._exploit_radio = ctk.CTkRadioButton(
            exploit_frame,
            text="ABadAvatar  (recomendado)",
            value="abadavatar",
            variable=ctk.StringVar(value="abadavatar"),
            fg_color="#107C10",
            hover_color="#107C10",
            state="disabled",
        )
        self._exploit_radio.pack(anchor="w", padx=14, pady=(2, 0))

        ctk.CTkLabel(
            exploit_frame,
            text="Exploit de avatar corrupto — no permanente",
            font=ctk.CTkFont(size=10),
            text_color="#555555",
        ).pack(anchor="w", padx=32, pady=(2, 10))

        # ── Payload ───────────────────────────────────────────
        payload_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)
        payload_frame.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="nsew")

        ctk.CTkLabel(
            payload_frame,
            text="Payload",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#aaaaaa",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self._radio_xeu = ctk.CTkRadioButton(
            payload_frame,
            text="XeUnshackle",
            value="xeunshackle",
            variable=self.payload_var,
            fg_color="#107C10",
            hover_color="#0d6a0d",
        )
        self._radio_xeu.pack(anchor="w", padx=14, pady=(2, 4))
        self._toggleable.append(self._radio_xeu)

        self._radio_fmx = ctk.CTkRadioButton(
            payload_frame,
            text="FreeMyXe",
            value="freemyxe",
            variable=self.payload_var,
            fg_color="#107C10",
            hover_color="#0d6a0d",
        )
        self._radio_fmx.pack(anchor="w", padx=14, pady=(0, 10))
        self._toggleable.append(self._radio_fmx)

        # ── Homebrew ──────────────────────────────────────────
        hb_frame = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=8)
        hb_frame.grid(row=1, column=0, columnspan=2, pady=4, sticky="ew")
        hb_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            hb_frame,
            text="Homebrew",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#aaaaaa",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 4))

        self._nand_cb = ctk.CTkCheckBox(
            hb_frame,
            text="NAND Flasher  (recomendado)",
            variable=self.nand_var,
            fg_color="#107C10",
            hover_color="#0d6a0d",
        )
        self._nand_cb.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="w")
        self._toggleable.append(self._nand_cb)

        ctk.CTkCheckBox(
            hb_frame,
            text="Aurora  (instalación manual)",
            fg_color="#555555",
            hover_color="#555555",
            state="disabled",
            text_color="#555555",
        ).grid(row=1, column=1, padx=14, pady=(0, 10), sticky="w")

        ctk.CTkCheckBox(
            hb_frame,
            text="XeXMenu  (instalación manual)",
            fg_color="#555555",
            hover_color="#555555",
            state="disabled",
            text_color="#555555",
        ).grid(row=1, column=2, padx=14, pady=(0, 10), sticky="w")

    def get_options(self) -> dict:
        return {
            "payload": self.payload_var.get(),
            "nand_flasher": self.nand_var.get(),
        }

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in self._toggleable:
            w.configure(state=state)
