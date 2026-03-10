import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageSequence
import cv2

ASCII = " .:-=+*#%@abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def pixel_to_ascii(value):
    return ASCII[int(value / 256 * len(ASCII))]

def convert_frame(img, width=120):
    ratio = img.height / img.width
    height = int(width * ratio * 0.55)
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
            char = char[0]
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

def process_image(file, out_dir):
    img = Image.open(file)
    width, height, rows = convert_frame(img)
    save_coltxt(os.path.join(out_dir, "0000.coltxt"), width, height, rows)

def process_gif(file, out_dir):
    img = Image.open(file)
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        frame = frame.convert("RGB")
        width, height, rows = convert_frame(frame)
        save_coltxt(os.path.join(out_dir, f"{i:04}.coltxt"), width, height, rows)

def process_video(file, out_dir, width=120):
    cap = cv2.VideoCapture(file)
    frame_id = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        w, h, rows = convert_frame(img, width)
        save_coltxt(os.path.join(out_dir, f"{frame_id:04}.coltxt"), w, h, rows)
        frame_id += 1
        root.update()
    cap.release()

def generate():
    file = filedialog.askopenfilename(title="Select image, GIF, or video")
    if not file:
        return
    out_dir = filedialog.askdirectory(title="Select output folder")
    if not out_dir:
        return

    ext = file.split(".")[-1].lower()
    if ext in ["png", "jpg", "jpeg", "bmp", "webp"]:
        process_image(file, out_dir)
    elif ext in ["gif"]:
        process_gif(file, out_dir)
    else:
        process_video(file, out_dir)

root = tk.Tk()
root.title("COLTXT Generator")

btn = tk.Button(root, text="Select File", command=generate)
btn.pack(padx=20, pady=20)

status = tk.Label(root, text="")
status.pack()

root.mainloop()