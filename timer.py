#!/usr/bin/env python3
import sys, os, subprocess, glob, atexit

PID_DIR   = "/tmp/timer_pids"
FONT_PATH = os.path.expanduser("~/Library/Fonts/DSEG7Classic-Regular.ttf")

def parse_duration(arg):
    total, cur = 0, ""
    for ch in arg:
        if ch.isdigit(): cur += ch
        elif ch in "hHmMsS" and cur:
            n = int(cur)
            if ch in "hH": total += n * 3600
            elif ch in "mM": total += n * 60
            elif ch in "sS": total += n
            cur = ""
    if cur: total += int(cur)
    return total

def fmt(s):
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

if len(sys.argv) < 2:
    print("Usage: timer 5m | 30s | 1h30m [label]  |  timer pomo  |  timer stop")
    sys.exit(1)

if sys.argv[1] == "stop":
    for f in glob.glob(f"{PID_DIR}/*"):
        try:
            os.kill(int(os.path.basename(f)), 15)
            os.remove(f)
        except: pass
    sys.exit(0)

POMO = sys.argv[1].lower() in ("pomo", "pomodoro")

if POMO:
    cycles = [
        (25*60, "WORK"), (5*60, "BREAK"),
        (25*60, "WORK"), (5*60, "BREAK"),
        (25*60, "WORK"), (5*60, "BREAK"),
        (25*60, "WORK"), (15*60, "LONG BREAK"),
    ]
else:
    d = parse_duration(sys.argv[1])
    if d <= 0:
        print("Couldn't parse duration. Try: 5m, 90s, 1h30m")
        sys.exit(1)
    cycles = [(d, " ".join(sys.argv[2:]))]

if not os.environ.get("_TIMER_BG"):
    env = os.environ.copy()
    env["_TIMER_BG"] = "1"
    subprocess.Popen([sys.argv[0]] + sys.argv[1:], env=env,
                     start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sys.exit(0)

os.makedirs(PID_DIR, exist_ok=True)
pid_file = f"{PID_DIR}/{os.getpid()}"
open(pid_file, "w").close()
atexit.register(lambda: os.path.exists(pid_file) and os.remove(pid_file))

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QFontDatabase, QPainterPath

PHASES = {
    "WORK":       ("#ff8c00", 160),
    "BREAK":      ("#4fc3f7",  80),
    "LONG BREAK": ("#81c784",  80),
    "":           ("#ff8c00", 140),
}

class TimerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cycles    = cycles
        self.cycle_idx = 0
        self.remaining = 0
        self.total     = 0
        self.progress  = 1.0
        self.bar_color = QColor("#ff8c00")
        self._drag     = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(210, 95)

        # load font
        fid = QFontDatabase.addApplicationFont(FONT_PATH)
        fams = QFontDatabase.applicationFontFamilies(fid)
        digit_family = fams[0] if fams else "Courier"

        self.time_lbl = QLabel(self)
        self.time_lbl.setGeometry(0, 8, 210, 58)
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setFont(QFont(digit_family, 44))

        self.phase_lbl = QLabel(self)
        self.phase_lbl.setGeometry(0, 66, 210, 20)
        self.phase_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase_lbl.setFont(QFont("Helvetica Neue", 9))
        self.phase_lbl.setStyleSheet("color: #555555; letter-spacing: 2px;")

        close = QLabel("✕", self)
        close.setGeometry(188, 6, 16, 16)
        close.setFont(QFont("Helvetica", 10))
        close.setStyleSheet("color: #333333;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.mousePressEvent = lambda e: self.close()
        close.enterEvent = lambda e: close.setStyleSheet("color: #888888;")
        close.leaveEvent = lambda e: close.setStyleSheet("color: #333333;")

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20, 20)

        self.load_cycle(0)

        self.ticker = QTimer()
        self.ticker.timeout.connect(self.tick)
        self.ticker.start(1000)

    def load_cycle(self, idx):
        dur, phase = self.cycles[idx]
        self.remaining = dur
        self.total     = dur
        self.progress  = 1.0

        key = "LONG BREAK" if "LONG" in phase.upper() else \
              "BREAK"      if "BREAK" in phase.upper() else \
              "WORK"       if "WORK" in phase.upper() else ""
        color, blur = PHASES.get(key, ("#ff8c00", 140))
        self.bar_color = QColor(color)

        self.time_lbl.setStyleSheet(f"color: {color};")
        self.phase_lbl.setText(phase.upper())

        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(color))
        glow.setBlurRadius(blur)
        glow.setOffset(0, 0)
        self.time_lbl.setGraphicsEffect(glow)

        self.time_lbl.setText(fmt(dur))
        self.update()

    def tick(self):
        self.remaining -= 1
        self.progress = self.remaining / self.total
        self.time_lbl.setText(fmt(self.remaining))
        self.update()

        if self.remaining == 0:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
            nxt = self.cycle_idx + 1
            if nxt < len(self.cycles):
                self.cycle_idx = nxt
                QTimer.singleShot(1500, lambda: self.load_cycle(self.cycle_idx))
            else:
                self.bar_color = QColor("#e74c3c")
                self.phase_lbl.setText("DONE")
                QTimer.singleShot(2000, QApplication.instance().quit)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()

        bg = QPainterPath()
        bg.addRoundedRect(QRectF(0, 0, W, H), 12, 12)
        p.fillPath(bg, QColor("#111111"))

        dim = QPainterPath()
        dim.addRoundedRect(QRectF(0, 0, W, 3), 1, 1)
        p.fillPath(dim, QColor("#2a2a2a"))

        bw = int(W * self.progress)
        if bw > 0:
            bar = QPainterPath()
            bar.addRoundedRect(QRectF(0, 0, bw, 3), 1, 1)
            p.fillPath(bar, self.bar_color)

        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

app = QApplication(sys.argv)
win = TimerWindow()
win.show()
sys.exit(app.exec())
