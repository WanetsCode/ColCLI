import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageSequence
import cv2

ASCII = " .:-=+*#%@abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def pixel_to_ascii(value):
    return ASCII[int(value / 256 * len(ASCII))]

def convert_frame(img, width=120):
    ratio = img.height / img.width
    height = int(width * ratio * 0.55)
    if height < 1:
        height = 1
    img = img.resize((width, height))
    img = img.convert("RGB")
    pixels = img.load()
    rows = []
    for y in range(height):
        row_cells = []
        for x in range(width):
            r, g, b = pixels[x, y]
            gray = int((r + g + b) / 3)
            char = pixel_to_ascii(gray)
            row_cells.append(f"{r},{g},{b},{char}")
        rows.append(" ".join(row_cells))
    return width, height, rows

def save_coltxt(path, width, height, rows):
    with open(path, "w", encoding="utf8") as f:
        f.write("#COLTXT\n")
        f.write(f"width={width}\n")
        f.write(f"height={height}\n")
        for r in rows:
            f.write(r + "\n")

def process_image(file, out_dir, width, log):
    img = Image.open(file)
    w, h, rows = convert_frame(img, width)
    save_coltxt(os.path.join(out_dir, "0000.coltxt"), w, h, rows)
    log("✓ Saved 0000.coltxt")

def process_gif(file, out_dir, width, log, progress_cb):
    img = Image.open(file)
    frames = list(ImageSequence.Iterator(img))
    total = len(frames)
    for i, frame in enumerate(frames):
        frame = frame.convert("RGB")
        w, h, rows = convert_frame(frame, width)
        save_coltxt(os.path.join(out_dir, f"{i:04}.coltxt"), w, h, rows)
        log(f"✓ Frame {i+1}/{total}")
        progress_cb(i + 1, total)

def process_video(file, out_dir, width, log, progress_cb):
    cap = cv2.VideoCapture(file)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        w, h, rows = convert_frame(img, width)
        save_coltxt(os.path.join(out_dir, f"{frame_id:04}.coltxt"), w, h, rows)
        frame_id += 1
        log(f"✓ Frame {frame_id}/{total if total > 0 else '?'}")
        progress_cb(frame_id, total if total > 0 else frame_id + 1)
    cap.release()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("COLTXT Encoder")
        self.configure(bg="#0d0d0d")
        self.resizable(False, False)
        self.geometry("620x700")

        self._selected_file = tk.StringVar(value="")
        self._out_dir = tk.StringVar(value="")
        self._width = tk.IntVar(value=120)
        self._status = tk.StringVar(value="")
        self._running = False

        self._build_ui()

    def _font(self, size, weight="normal"):
        return ("Courier", size, weight)

    def _build_ui(self):
        header = tk.Frame(self, bg="#0d0d0d")
        header.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(header, text="COLTXT", font=("Courier", 28, "bold"),
                 bg="#0d0d0d", fg="#00ff99").pack(side="left")
        tk.Label(header, text=" ENCODER", font=("Courier", 28),
                 bg="#0d0d0d", fg="#ffffff").pack(side="left")

        tk.Label(self, text="Convert images, GIFs and videos to the COLTXT format\nfor use with ColCLI and Cloudflare Workers.",
                 font=self._font(10), bg="#0d0d0d", fg="#666666",
                 justify="left").pack(anchor="w", padx=30, pady=(6, 20))

        self._section("① INPUT FILE")
        row = tk.Frame(self, bg="#0d0d0d")
        row.pack(fill="x", padx=30, pady=(4, 0))
        self._file_label = tk.Label(row, textvariable=self._selected_file,
                                    text="No file selected", font=self._font(10),
                                    bg="#1a1a1a", fg="#888888", anchor="w",
                                    width=46, relief="flat", padx=10, pady=8)
        self._file_label.pack(side="left")
        tk.Button(row, text="Browse", command=self._pick_file,
                  font=self._font(10, "bold"), bg="#00ff99", fg="#0d0d0d",
                  relief="flat", padx=12, pady=8, cursor="hand2",
                  activebackground="#00cc77", activeforeground="#0d0d0d",
                  bd=0).pack(side="left", padx=(8, 0))

        tk.Label(self, text="Supported: PNG, JPG, BMP, WEBP, GIF, MP4, AVI, MOV, MKV",
                 font=self._font(9), bg="#0d0d0d", fg="#444444").pack(anchor="w", padx=30, pady=(4, 16))

        self._section("② OUTPUT FOLDER")
        row2 = tk.Frame(self, bg="#0d0d0d")
        row2.pack(fill="x", padx=30, pady=(4, 0))
        tk.Label(row2, textvariable=self._out_dir,
                 text="No folder selected", font=self._font(10),
                 bg="#1a1a1a", fg="#888888", anchor="w",
                 width=46, relief="flat", padx=10, pady=8).pack(side="left")
        tk.Button(row2, text="Browse", command=self._pick_dir,
                  font=self._font(10, "bold"), bg="#00ff99", fg="#0d0d0d",
                  relief="flat", padx=12, pady=8, cursor="hand2",
                  activebackground="#00cc77", activeforeground="#0d0d0d",
                  bd=0).pack(side="left", padx=(8, 0))

        tk.Label(self, text="Frames will be saved as 0000.coltxt, 0001.coltxt, ...",
                 font=self._font(9), bg="#0d0d0d", fg="#444444").pack(anchor="w", padx=30, pady=(4, 16))

        self._section("③ WIDTH  (characters)")
        row3 = tk.Frame(self, bg="#0d0d0d")
        row3.pack(fill="x", padx=30, pady=(4, 0))

        self._width_display = tk.Label(row3, text="120", font=self._font(13, "bold"),
                                       bg="#0d0d0d", fg="#00ff99", width=5, anchor="w")
        self._width_display.pack(side="left")

        slider = tk.Scale(row3, from_=40, to=240, orient="horizontal",
                          variable=self._width, bg="#0d0d0d", fg="#ffffff",
                          troughcolor="#1a1a1a", highlightthickness=0,
                          activebackground="#00ff99", sliderrelief="flat",
                          length=320, showvalue=False,
                          command=lambda v: self._width_display.config(text=v))
        slider.pack(side="left", padx=(0, 10))

        tk.Label(row3, text="← narrow   wide →", font=self._font(9),
                 bg="#0d0d0d", fg="#444444").pack(side="left")

        tk.Label(self,
                 text="Higher width = more detail but larger files and slower rendering.",
                 font=self._font(9), bg="#0d0d0d", fg="#444444").pack(anchor="w", padx=30, pady=(2, 20))

        self._convert_btn = tk.Button(self, text="▶  CONVERT", command=self._start,
                                      font=self._font(13, "bold"), bg="#00ff99", fg="#0d0d0d",
                                      relief="flat", padx=20, pady=12, cursor="hand2",
                                      activebackground="#00cc77", activeforeground="#0d0d0d", bd=0)
        self._convert_btn.pack(padx=30, pady=(0, 16), fill="x")

        prog_frame = tk.Frame(self, bg="#0d0d0d")
        prog_frame.pack(fill="x", padx=30)
        self._progress = ttk.Progressbar(prog_frame, mode="determinate", length=560)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor="#1a1a1a", background="#00ff99",
                        bordercolor="#0d0d0d", lightcolor="#00ff99", darkcolor="#00ff99")
        self._progress.pack(fill="x")

        self._log_frame = tk.Frame(self, bg="#111111", relief="flat")
        self._log_frame.pack(fill="both", expand=True, padx=30, pady=(12, 20))

        self._log_text = tk.Text(self._log_frame, bg="#111111", fg="#00ff99",
                                 font=("Courier", 9), relief="flat", state="disabled",
                                 height=8, wrap="word", padx=10, pady=8,
                                 insertbackground="#00ff99", bd=0)
        self._log_text.pack(fill="both", expand=True)

        self._guide_section()

    def _section(self, label):
        tk.Label(self, text=label, font=self._font(10, "bold"),
                 bg="#0d0d0d", fg="#00ff99").pack(anchor="w", padx=30, pady=(0, 2))

    def _guide_section(self):
        guide = tk.Frame(self, bg="#141414", relief="flat")
        guide.pack(fill="x", padx=30, pady=(0, 24))
        tk.Label(guide, text="QUICK GUIDE", font=("Courier", 9, "bold"),
                 bg="#141414", fg="#555555").pack(anchor="w", padx=12, pady=(10, 4))
        tips = [
            "1. Select your source file (image, GIF, or video).",
            "2. Choose an empty output folder — frames go there.",
            "3. Adjust width. 80–120 works well for terminals.",
            "4. Click CONVERT. Each frame becomes a .coltxt file.",
            "5. Upload the folder to GitHub under /frames/.",
            "6. Point your Cloudflare Worker at the GitHub URL.",
            "7. Run:  curl https://your-worker.workers.dev",
        ]
        for tip in tips:
            tk.Label(guide, text=tip, font=("Courier", 9),
                     bg="#141414", fg="#555555", anchor="w",
                     justify="left").pack(anchor="w", padx=12)
        tk.Label(guide, text="", bg="#141414").pack(pady=4)

    def _pick_file(self):
        f = filedialog.askopenfilename(
            title="Select image, GIF, or video",
            filetypes=[("Media files", "*.png *.jpg *.jpeg *.bmp *.webp *.gif *.mp4 *.avi *.mov *.mkv *.webm"),
                       ("All files", "*.*")]
        )
        if f:
            self._selected_file.set(f)
            self._file_label.config(fg="#ffffff")

    def _pick_dir(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self._out_dir.set(d)

    def _log(self, msg):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _set_progress(self, done, total):
        pct = (done / total * 100) if total > 0 else 0
        self._progress["value"] = pct
        self.update_idletasks()

    def _start(self):
        if self._running:
            return
        file = self._selected_file.get()
        out_dir = self._out_dir.get()
        if not file or not os.path.isfile(file):
            self._log("✗ Please select a valid input file.")
            return
        if not out_dir or not os.path.isdir(out_dir):
            self._log("✗ Please select a valid output folder.")
            return

        self._running = True
        self._convert_btn.config(state="disabled", text="Converting…")
        self._progress["value"] = 0
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")

        width = self._width.get()
        threading.Thread(target=self._run, args=(file, out_dir, width), daemon=True).start()

    def _run(self, file, out_dir, width):
        ext = file.rsplit(".", 1)[-1].lower()
        try:
            self._log(f"Starting conversion → {out_dir}")
            if ext in ("png", "jpg", "jpeg", "bmp", "webp"):
                process_image(file, out_dir, width, self._log)
                self._set_progress(1, 1)
            elif ext == "gif":
                process_gif(file, out_dir, width, self._log, self._set_progress)
            else:
                process_video(file, out_dir, width, self._log, self._set_progress)
            self._log("✓ Done!")
        except Exception as e:
            self._log(f"✗ Error: {e}")
        finally:
            self._running = False
            self._convert_btn.config(state="normal", text="▶  CONVERT")


if __name__ == "__main__":
    app = App()
    app.mainloop()