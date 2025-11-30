import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from tkinterdnd2 import DND_FILES, TkinterDnD
from skimage import io
from PIL import Image, ImageTk

from main import analyser_image_numpy
from src.debug_utils import visualiser_detection_detaillee


class KeyboardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Détection de layout de clavier")

        # Grande taille de base
        self.root.geometry("1100x700")
        self.root.minsize(800, 600)

        # Essaie de maximiser la fenêtre (Windows)
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        # Couleurs / style
        self.bg_main = "#1e1e2f"
        self.bg_card = "#26263a"
        self.accent = "#4CAF50"
        self.accent_hover = "#66BB6A"
        self.text_main = "#ffffff"
        self.text_muted = "#bbbbcc"

        self.root.configure(bg=self.bg_main)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Card.TFrame",
            background=self.bg_card,
            relief="flat",
        )
        style.configure(
            "TLabel",
            background=self.bg_card,
            foreground=self.text_main,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.bg_main,
            foreground=self.text_main,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background=self.bg_card,
            foreground=self.text_muted,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.accent,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            padding=6,
            borderwidth=0,
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.accent_hover)],
        )

        # Conteneur principal
        outer = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ttk.Label(
            outer,
            text="🔍 Détection de layout de clavier",
            style="Title.TLabel",
            background=self.bg_card,
        )
        header.pack(anchor="w", pady=(0, 10))

        # Zone centrale
        center = ttk.Frame(outer, style="Card.TFrame")
        center.pack(fill="both", expand=True)

        # Zone de drop
        self.drop_label = tk.Label(
            center,
            text="Glisse une image de clavier ici\nou clique sur \"Choisir une image\"",
            bg=self.bg_main,
            fg=self.text_muted,
            relief="ridge",
            bd=2,
            width=50,
            height=8,
            font=("Segoe UI", 11),
            justify="center",
        )
        self.drop_label.pack(fill="x", pady=(0, 10))

        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        # Ligne de boutons
        btn_bar = ttk.Frame(center, style="Card.TFrame")
        btn_bar.pack(fill="x", pady=(0, 10))

        self.image_path = None

        self.btn_load = ttk.Button(
            btn_bar,
            text="Choisir une image…",
            style="Primary.TButton",
            command=self.load_image,
        )
        self.btn_load.pack(side="left", padx=(0, 10))

        self.btn_run = ttk.Button(
            btn_bar,
            text="Analyser",
            style="Primary.TButton",
            command=self.run_analysis,
        )
        self.btn_run.pack(side="left")

        # Zone de résultat (badge + texte multi-ligne)
        self.result_frame = ttk.Frame(center, style="Card.TFrame")
        self.result_frame.pack(fill="x", pady=(5, 0))

        self.result_label = tk.Label(
            self.result_frame,
            text="Aucune image sélectionnée.",
            bg="#33334d",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            padx=12,
            pady=8,
            anchor="w",
            justify="left",
        )
        self.result_label.pack(fill="x")

        # Zone d'aperçu de l'image analysée
        self.preview_label = tk.Label(
            center,
            bg=self.bg_card,
        )
        self.preview_label.pack(fill="both", expand=True, pady=(10, 0))
        self._preview_photo = None  # référence pour éviter le GC

    def set_selected_image(self, path: str):
        self.image_path = path
        self.result_label.config(
            text=f"📂 Image sélectionnée : {path}",
            bg="#33334d",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )
        # Efface l'aperçu précédent
        self.preview_label.config(image="")
        self._preview_photo = None

    def on_drop(self, event):
        path = event.data.strip().strip("{}")
        if path:
            self.set_selected_image(path)

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.tif")]
        )
        if not path:
            return
        self.set_selected_image(path)

    def run_analysis(self):
        if not self.image_path:
            messagebox.showwarning("Attention", "Choisis ou glisse d'abord une image.")
            return

        try:
            img = io.imread(self.image_path)
            res = analyser_image_numpy(img)

            verdict = res["verdict"]
            debug = res["debug"]

            layout = verdict.get("LAYOUT", "?")
            os_ = verdict.get("MAC_WIN", "?")
            fmt = verdict.get("ISO_ANSI", "?")

            # Quelques métriques techniques "comme dans le main"
            nb_touches = debug.get("TouchesCount", debug.get("Touches", "?"))
            shift_ratio = debug.get("ShiftRatio", "?")
            enter_ratio = debug.get("EnterRatioHL", "?")
            tl_center = debug.get("TLCenterY", "?")
            tl_extent = debug.get("TLExtent", "?")

            text = (
                f"✅ RÉSULTATS DE L'ANALYSE\n"
                f"   Format  : {fmt}\n"
                f"   Système : {os_}\n"
                f"   Layout  : {layout}\n"
                f"------------------------------------\n"
                f"   Touches détectées : {nb_touches}\n"
                f"   ShiftRatio        : {shift_ratio}\n"
                f"   EnterRatioHL      : {enter_ratio}\n"
                f"   TLCenterY         : {tl_center}\n"
                f"   TLExtent          : {tl_extent}"
            )

            # Prépare le chemin de sauvegarde pour l'image d'analyse
            basename = os.path.basename(self.image_path).split(".")[0]
            result_dir = os.path.join("data", "result")
            os.makedirs(result_dir, exist_ok=True)
            save_path = os.path.join(result_dir, f"{basename}_analyse.png")

            # Génère et sauvegarde la visualisation détaillée
            visualiser_detection_detaillee(
                res["img"],
                res["touches"],
                res["rois"],
                res["verdict"],
                res["debug"],
                save_path=save_path,
            )

            # Badge vert + texte détaillé + info sur le PNG
            self.result_label.config(
                text=text + f"\n\n   📁 Image enregistrée : {save_path}",
                bg="#2e7d32",
                fg="#ffffff",
                font=("Segoe UI", 11, "bold"),
            )

            # Afficher l'image d'analyse dans l'interface
            try:
                img_pil = Image.open(save_path)

                # Adapter la taille à la zone d'aperçu
                max_w, max_h = 1000, 350
                w, h = img_pil.size
                scale = min(max_w / w, max_h / h, 1.0)
                if scale < 1.0:
                    img_pil = img_pil.resize(
                        (int(w * scale), int(h * scale)), Image.LANCZOS
                    )

                self._preview_photo = ImageTk.PhotoImage(img_pil)
                self.preview_label.config(image=self._preview_photo)
            except Exception as e:
                print(f"Erreur lors du chargement de l'aperçu: {e}")

        except Exception as e:
            self.result_label.config(
                text=f"❌ Erreur: {e}",
                bg="#b71c1c",
                fg="#ffffff",
                font=("Segoe UI", 11, "bold"),
            )
            messagebox.showerror("Erreur", str(e))


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = KeyboardGUI(root)
    root.mainloop()
