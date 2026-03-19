import os
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ─────────────────────────────────────────────────────────────────────────────
#  Processing logic  (runs in background thread)
# ─────────────────────────────────────────────────────────────────────────────

def run_processing(import_dir, export_dir, mode, log_callback, done_callback):
    """
    mode values:
      'poisson_glb'  — Screened Poisson reconstruction → export GLB
      'poisson_dae'  — Screened Poisson reconstruction → export DAE
      'convert_glb'  — Direct DAE → GLB conversion (no remeshing)
    """

    # ── Validate dependencies ────────────────────────────────────────────────
    if mode in ('poisson_glb', 'poisson_dae'):
        try:
            import pymeshlab
        except ImportError:
            log_callback("ERROR: pymeshlab is not installed. Run: pip install pymeshlab")
            done_callback(success=False)
            return

    if mode in ('poisson_glb', 'convert_glb'):
        try:
            import trimesh
        except ImportError:
            log_callback("ERROR: trimesh is not installed. Run: pip install trimesh")
            done_callback(success=False)
            return

    if mode == 'convert_glb':
        try:
            import collada  # pycollada — trimesh uses this to read DAE files
        except ImportError:
            log_callback("ERROR: pycollada is not installed. Run: pip install pycollada")
            done_callback(success=False)
            return

    # ── Collect files ────────────────────────────────────────────────────────
    files = [
        os.path.join(import_dir, f)
        for f in os.listdir(import_dir)
        if f.startswith('Morphology') and f.endswith('.dae')
    ]

    if not files:
        log_callback("No files found matching 'Morphology*.dae' in the selected folder.")
        done_callback(success=False)
        return

    os.makedirs(export_dir, exist_ok=True)
    ext = 'dae' if mode == 'poisson_dae' else 'glb'
    log_callback(f"Found {len(files)} file(s).  Mode: {mode}  →  .{ext}\n")

    # ── Set up pymeshlab once if needed ─────────────────────────────────────
    ms = None
    if mode in ('poisson_glb', 'poisson_dae'):
        ms = pymeshlab.MeshSet()

    # ── Process each file ────────────────────────────────────────────────────
    for i, f in enumerate(files, 1):
        base_name   = os.path.splitext(os.path.basename(f))[0]
        output_path = os.path.join(export_dir, f"{base_name}.{ext}")
        log_callback(f"[{i}/{len(files)}] {os.path.basename(f)}")

        try:
            # ── Mode A: Poisson reconstruction → DAE ────────────────────────
            if mode == 'poisson_dae':
                ms.load_new_mesh(f)
                ms.generate_surface_reconstruction_screened_poisson(depth=10, preclean=True)
                ms.save_current_mesh(output_path)

            # ── Mode B: Poisson reconstruction → GLB ────────────────────────
            elif mode == 'poisson_glb':
                ms.load_new_mesh(f)
                ms.generate_surface_reconstruction_screened_poisson(depth=10, preclean=True)
                with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    ms.save_current_mesh(tmp_path)
                    mesh = trimesh.load(tmp_path)
                    mesh.export(output_path)
                finally:
                    os.remove(tmp_path)

            # ── Mode C: Direct conversion DAE → GLB (no remeshing) ──────────
            elif mode == 'convert_glb':
                mesh = trimesh.load(f, force='mesh')
                mesh.export(output_path)

            log_callback(f"  ✓ Saved: {output_path}")

        except Exception as e:
            log_callback(f"  ✗ ERROR: {e}")

    log_callback("\nAll done!")
    done_callback(success=True)


# ─────────────────────────────────────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VikingMesh Processor")
        self.resizable(False, False)

        # ── Palette ──────────────────────────────────────────────────────────
        BG        = "#16161e"
        PANEL     = "#1e1e2a"
        ACCENT    = "#c0392b"        # Viking red
        ACCENT_HV = "#e74c3c"
        GOLD      = "#c9a84c"        # Norse gold accent
        FG        = "#e8e4d8"
        FG_DIM    = "#7a7468"
        ENTRY_BG  = "#0e0e14"
        BORDER    = "#2e2e3a"

        TITLE_FONT = ("Segoe UI",  17, "bold")
        SUB_FONT   = ("Segoe UI",   8)
        LABEL_FONT = ("Segoe UI",   7, "bold")
        ENTRY_FONT = ("Consolas",   9)
        BTN_FONT   = ("Segoe UI",  10, "bold")
        RB_FONT    = ("Segoe UI",   9, "bold")
        LOG_FONT   = ("Consolas",   9)
        DESC_FONT  = ("Segoe UI",   7)

        self.configure(bg=BG)

        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT, pady=0)
        hdr.pack(fill="x")

        # decorative gold stripe
        tk.Frame(hdr, bg=GOLD, height=3).pack(fill="x")

        inner_hdr = tk.Frame(hdr, bg=ACCENT, padx=24, pady=12)
        inner_hdr.pack(fill="x")

        tk.Label(inner_hdr, text="⚔  VikingMesh Processor",
                 font=TITLE_FONT, fg="white", bg=ACCENT,
                 anchor="w").pack(anchor="w")
        tk.Label(inner_hdr,
                 text="DAE mesh reconstruction & conversion  ·  Blender 5.0+ ready",
                 font=SUB_FONT, fg="#f5c6c0", bg=ACCENT,
                 anchor="w").pack(anchor="w")

        tk.Frame(hdr, bg=GOLD, height=3).pack(fill="x")

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG, padx=26, pady=18)
        body.pack(fill="both")

        def section_label(text):
            tk.Label(body, text=text, font=LABEL_FONT,
                     fg=GOLD, bg=BG).pack(anchor="w", pady=(14, 3))

        def folder_row(label_text, var):
            section_label(label_text)
            row = tk.Frame(body, bg=BG)
            row.pack(fill="x")
            entry = tk.Entry(row, textvariable=var, font=ENTRY_FONT,
                             bg=ENTRY_BG, fg=FG, insertbackground=FG,
                             relief="flat", bd=0,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT,
                             width=46)
            entry.pack(side="left", ipady=6, padx=(0, 8))

            def browse(v=var):
                path = filedialog.askdirectory()
                if path:
                    v.set(path)

            tk.Button(row, text="Browse", font=("Segoe UI", 8, "bold"),
                      bg=PANEL, fg=FG,
                      activebackground=ACCENT, activeforeground="white",
                      relief="flat", bd=0, padx=12, pady=5,
                      cursor="hand2", command=browse).pack(side="left")

        self.import_var = tk.StringVar()
        self.export_var = tk.StringVar()
        folder_row("INPUT FOLDER  —  contains Morphology*.dae files", self.import_var)
        folder_row("OUTPUT FOLDER", self.export_var)

        # ── Mode selector ────────────────────────────────────────────────────
        section_label("PROCESSING MODE")

        self.mode_var = tk.StringVar(value="poisson_glb")

        modes = [
            ("poisson_glb",
             "Reconstruct → GLB",
             "Screened Poisson remesh  ·  export GLB  (Blender 5.0+, recommended)"),
            ("poisson_dae",
             "Reconstruct → DAE",
             "Screened Poisson remesh  ·  export DAE  (Blender 4.x / legacy)"),
            ("convert_glb",
             "Convert → GLB  (no remesh)",
             "Direct DAE → GLB conversion  ·  no reconstruction  ·  fast"),
        ]

        modes_frame = tk.Frame(body, bg=BG)
        modes_frame.pack(anchor="w", fill="x")

        for val, label, desc in modes:
            row = tk.Frame(modes_frame, bg=PANEL,
                           highlightthickness=1, highlightbackground=BORDER,
                           padx=12, pady=8)
            row.pack(fill="x", pady=3)

            rb = tk.Radiobutton(row, text=label,
                                variable=self.mode_var, value=val,
                                font=RB_FONT, fg=FG, bg=PANEL,
                                selectcolor=PANEL,
                                activebackground=PANEL,
                                activeforeground=ACCENT,
                                indicatoron=True, cursor="hand2",
                                anchor="w")
            rb.pack(anchor="w")
            tk.Label(row, text=desc, font=DESC_FONT,
                     fg=FG_DIM, bg=PANEL, anchor="w").pack(anchor="w")

        # ── Run button ───────────────────────────────────────────────────────
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(pady=(18, 4))

        self.run_btn = tk.Button(btn_row, text="⚔  Run",
                                 font=("Segoe UI", 11, "bold"),
                                 bg=ACCENT, fg="white",
                                 activebackground=ACCENT_HV,
                                 activeforeground="white",
                                 relief="flat", bd=0,
                                 padx=36, pady=10,
                                 cursor="hand2",
                                 command=self.start_processing)
        self.run_btn.pack()

        # ── Progress bar ─────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("VM.Horizontal.TProgressbar",
                        troughcolor=ENTRY_BG, background=GOLD,
                        thickness=3, borderwidth=0)
        self.progress = ttk.Progressbar(body, mode="indeterminate",
                                        length=460,
                                        style="VM.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(8, 0))

        # ── Log ──────────────────────────────────────────────────────────────
        section_label("LOG")
        log_outer = tk.Frame(body, bg=ENTRY_BG,
                             highlightthickness=1,
                             highlightbackground=BORDER)
        log_outer.pack(fill="both")

        self.log_box = tk.Text(log_outer, height=9, font=LOG_FONT,
                               bg=ENTRY_BG, fg=FG,
                               insertbackground=FG,
                               relief="flat", bd=8,
                               state="disabled", wrap="word")
        sb = tk.Scrollbar(log_outer, command=self.log_box.yview,
                          bg=PANEL, troughcolor=ENTRY_BG,
                          relief="flat", bd=0, width=10)
        self.log_box.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True)

        # ── Footer ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=GOLD, height=2).pack(fill="x")
        tk.Label(self, text="pymeshlab  ·  trimesh  ·  VikingMesh Processor",
                 font=("Segoe UI", 7), fg=FG_DIM, bg=BG).pack(pady=6)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def log(self, message):
        def _write():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _write)

    def set_running(self, running: bool):
        def _update():
            if running:
                self.run_btn.configure(state="disabled", text="Processing…")
                self.progress.start(12)
            else:
                self.run_btn.configure(state="normal", text="⚔  Run")
                self.progress.stop()
                self.progress["value"] = 0
        self.after(0, _update)

    def start_processing(self):
        import_dir = self.import_var.get().strip()
        export_dir = self.export_var.get().strip()
        mode       = self.mode_var.get()

        if not import_dir or not os.path.isdir(import_dir):
            messagebox.showerror("Missing input",
                                 "Please select a valid input folder.")
            return
        if not export_dir:
            messagebox.showerror("Missing output",
                                 "Please select an output folder.")
            return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        self.set_running(True)

        def done_callback(success):
            self.set_running(False)
            if success:
                self.after(0, lambda: messagebox.showinfo(
                    "Complete",
                    f"Processing finished!\n\nFiles saved to:\n{export_dir}"))

        threading.Thread(
            target=run_processing,
            args=(import_dir, export_dir, mode, self.log, done_callback),
            daemon=True
        ).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
