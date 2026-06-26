import webbrowser

import customtkinter as ctk


class FooterFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#0a0a0a", corner_radius=0, **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text=(
                "ABadAvatar by shutterbug2000  •  XeUnshackle by Byrom90  •  "
                "FreeMyXe by InvoxiPlayGames  •  NAND Flasher by Swizzy"
            ),
            font=ctk.CTkFont(size=9),
            text_color="#444444",
        ).pack(pady=(5, 0))

        links = ctk.CTkFrame(self, fg_color="transparent")
        links.pack(pady=(2, 6))

        def _link_btn(text, url):
            return ctk.CTkButton(
                links,
                text=text,
                command=lambda: webbrowser.open(url),
                fg_color="transparent",
                hover_color="#1a1a1a",
                text_color="#107C10",
                font=ctk.CTkFont(size=10),
                width=80,
                height=18,
            )

        _link_btn(
            "GitHub", "https://github.com/ohquebacan/OQB-BadStick-Mac"
        ).pack(side="left", padx=4)

        _link_btn(
            "ohquebacan.com", "https://ohquebacan.com"
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            links,
            text="BadStick (Windows)",
            command=lambda: webbrowser.open("https://github.com/LxcyDr0p/BadStick"),
            fg_color="transparent",
            hover_color="#1a1a1a",
            text_color="#444444",
            font=ctk.CTkFont(size=10),
            width=120,
            height=18,
        ).pack(side="left", padx=4)
