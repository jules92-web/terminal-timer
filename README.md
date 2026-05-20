# terminal-timer

A floating countdown timer for macOS with a retro LED display.

## Features

- Floating window that stays on top of everything
- DSEG7 LED-style font with glow effect
- Pomodoro mode (25m work / 5m break cycles)
- Plays a sound when time is up
- Draggable, close with ✕

## Install

```bash
pip3 install PyQt6
curl -sL "https://github.com/keshikan/DSEG/raw/master/fonts/DSEG7Classic-Regular.ttf" \
  -o ~/Library/Fonts/DSEG7Classic-Regular.ttf
cp timer.py ~/.local/bin/timer
chmod +x ~/.local/bin/timer
```

## Usage

```bash
timer 25m            # 25 minute timer
timer 1h30m          # 1 hour 30 minutes
timer 30s            # 30 seconds
timer 10m Deep Work  # with a label
timer pomo           # pomodoro mode
timer stop           # stop all running timers
```
