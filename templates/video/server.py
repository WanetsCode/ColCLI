import os
import time
from flask import Flask, request, redirect, Response

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "colcli.config")


def load_config():

    cfg = {}

    with open(CONFIG_FILE) as f:
        for line in f:
            if "=" in line:
                k,v = line.strip().split("=",1)
                cfg[k] = v

    cfg["fps"] = int(cfg.get("fps",10))
    cfg["frames"] = cfg.get("frames","frames")
    cfg["loop"] = cfg.get("loop","true") == "true"

    return cfg


def coltxt_to_ansi(path):
    out = []

    with open(path, encoding="utf8") as f:
        lines = f.readlines()[3:]

    for line in lines:
        cells = line.strip().split(" ")
        row = ""

        for cell in cells:
            if not cell:
                continue
            parts = cell.split(",")
            if len(parts) != 4:
                continue
            r, g, b, ch = parts
            row += f"\033[48;2;0;0;0m\033[38;2;{r};{g};{b}m{ch}"

        out.append(row)

    import shutil
    term_cols, term_rows = shutil.get_terminal_size()
    for i in range(len(out)):
        out[i] += " " * (term_cols - len(out[i]))
    while len(out) < term_rows:
        out.append(" " * term_cols)

    return "\n".join(out)


def stream_animation():
    cfg = load_config()
    frame_dir = os.path.join(BASE_DIR, cfg["frames"])
    fps = cfg["fps"]
    frames = sorted(os.listdir(frame_dir))
    delay = 1 / fps if fps > 0 else 0

    ansi_frames = [coltxt_to_ansi(os.path.join(frame_dir, f)) for f in frames]

    while True:
        for ansi in ansi_frames:
            yield "\033[H" + ansi
            time.sleep(delay)
        if not cfg["loop"]:
            break


@app.route("/")
def root():

    cfg = load_config()

    ua = request.headers.get("User-Agent", "").lower()

    is_terminal = any(x in ua for x in ["curl", "wget", "httpie", "python-requests"])

    if is_terminal:
        return Response(stream_animation(), mimetype="text/plain")

    if "browser_redirect" in cfg:
        return f"""
        <html>
            <head>
                <meta http-equiv="refresh" content="0;url={cfg['browser_redirect']}">
            </head>
            <body>
                <p>If you are not redirected automatically, <a href="{cfg['browser_redirect']}">click here</a></p>
            </body>
        </html>
        """, 200, {"Content-Type": "text/html"}

    return "No animation available.", 200, {"Content-Type": "text/plain"}

app.run(port=8080)