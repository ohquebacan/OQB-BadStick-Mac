import customtkinter as ctk


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, parent, app_name: str, app_version: str, **kwargs):
        super().__init__(parent, fg_color="#141414", corner_radius=0, **kwargs)
        self._build(app_name, app_version)

    def _build(self, app_name: str, app_version: str):
        ctk.CTkLabel(
            self,
            text=app_name,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#107C10",
        ).pack(pady=(14, 2))

        ctk.CTkLabel(
            self,
            text=f"v{app_version}  •  Preparador de USB para ABadAvatar exploit  •  Xbox 360",
            font=ctk.CTkFont(size=11),
            text_color="#666666",
        ).pack(pady=(0, 12))
