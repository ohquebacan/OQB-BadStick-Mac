import customtkinter as ctk


class DeviceFrame(ctk.CTkFrame):
    def __init__(self, parent, on_refresh, on_format, **kwargs):
        super().__init__(parent, fg_color="#1E1E1E", corner_radius=8, **kwargs)
        self.on_refresh = on_refresh
        self.on_format = on_format
        self.device_var = ctk.StringVar(value="Sin dispositivos USB detectados")
        self.devices: list = []
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Dispositivo USB",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#aaaaaa",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(10, 4))

        self.dropdown = ctk.CTkOptionMenu(
            self,
            variable=self.device_var,
            values=["Sin dispositivos USB detectados"],
            fg_color="#2d2d2d",
            button_color="#107C10",
            button_hover_color="#0d6a0d",
            dynamic_resizing=False,
        )
        self.dropdown.grid(row=1, column=0, padx=(14, 6), pady=(0, 12), sticky="ew")

        self.refresh_btn = ctk.CTkButton(
            self,
            text="⟳ Actualizar",
            command=self.on_refresh,
            fg_color="#2d2d2d",
            hover_color="#3d3d3d",
            width=110,
        )
        self.refresh_btn.grid(row=1, column=1, padx=4, pady=(0, 12))

        self.format_btn = ctk.CTkButton(
            self,
            text="Formatear FAT32",
            command=self.on_format,
            fg_color="#5a3000",
            hover_color="#7a4500",
            width=130,
        )
        self.format_btn.grid(row=1, column=2, padx=(4, 14), pady=(0, 12))

    def update_devices(self, devices: list):
        self.devices = devices
        if devices:
            values = [
                f"{d['name']} ({d['size']}) — /dev/{d['identifier']}"
                for d in devices
            ]
            self.dropdown.configure(values=values)
            self.device_var.set(values[0])
        else:
            self.dropdown.configure(values=["Sin dispositivos USB detectados"])
            self.device_var.set("Sin dispositivos USB detectados")

    def get_selected_device(self) -> dict:
        if not self.devices:
            return None
        selected = self.device_var.get()
        for d in self.devices:
            label = f"{d['name']} ({d['size']}) — /dev/{d['identifier']}"
            if label == selected:
                return d
        return self.devices[0]

    def set_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.dropdown.configure(state=state)
        self.refresh_btn.configure(state=state)
        self.format_btn.configure(state=state)
