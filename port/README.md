# FrickBears 3 — Android Port

Unofficial Android port of **Five Nights at Frickbear's 3** by
[SpookyRick](https://gamejolt.com/@SpookyRick), built on
[Butterscotch](https://github.com/ButterscotchRunner/Butterscotch) — an
open-source (AGPL-3.0) re-implementation of the GameMaker: Studio runner.

The game itself is a GameMaker: Studio 2.3 title, so there is no Android
export of it; this port runs the original `data.win` unmodified inside a
GameMaker-compatible runtime and layers a purpose-built **touch control
overlay** on top.

> This is an unofficial fan port. *Five Nights at Frickbear's 3* and all of its
> assets belong to SpookyRick. Please support the original game.

---

## What this port actually is

| | |
| --- | --- |
| Game engine | GameMaker: Studio 2.3 (WAD v17), bytecode |
| Runtime | [Butterscotch](https://github.com/ButterscotchRunner/Butterscotch) (AGPL-3.0) |
| Port layer | A Kotlin touch overlay + a small native room-query accessor |
| Game data | The original `data.win`, texture groups and audio groups, untouched |

The port does **not** modify the game. The original `data.win` is loaded as-is,
so every mechanic, sound, minigame and ending behaves exactly as SpookyRick
shipped it. The port only adds an input layer.

---

## The control scheme

FB3's night loop is: watch the **monitor**, check the **hallways** with the
**flashlight**, and slam the **left/right door** when something reaches the
office. Power drains while doors are shut and the fan is running, so you can
never hold a door down forever — every tap has to count.

The overlay puts the four highest-frequency actions in the thumb zone:

| Button | Default key | Action |
| --- | --- | --- |
| `LIGHT` | `S` | Toggle the flashlight |
| `L.DOOR` | `A` | Toggle the left door |
| `R.DOOR` | `D` | Toggle the right door |
| `MONITOR` | `W` | Raise / lower the monitor |

Plus a **horizontal swipe** anywhere on the game surface to step through the
monitor's camera tabs.

FB3 also has its own in-game *Controls Options* screen that remaps keyboard
and mouse input, so the keys above are only defaults — remap them in-game to
match however you like, and remap the overlay buttons to match in the layout
editor.

### Why the controls feel the way they do

The brief for this port was that FB3 is a hard game and you have to be able to
*flow* through it. The design decisions that follow from that:

- **Buttons fire on press, not on release.** A release-triggered button adds
  ~80 ms of perceived latency per action, which is very noticeable when you
  are reacting to a jumpscare.
- **Sliding off a button does not cancel it.** Under stress, thumbs drift.
  A cancel-on-slide would silently drop a door and get you killed.
- **Doors and the monitor toggle.** They are latched actions in the game;
  hold-to-activate would mean keeping a finger planted and losing it when you
  need that thumb for something else.
- **Buttons are sized as a fraction of the viewport**, so they stay comfortable
  on a 5" phone and a 10" tablet alike.
- **Haptics on every press**, so you can confirm an action without taking your
  eyes off the monitor.
- **The overlay hides itself** on the title screen, the shop, the salvage
  maze and the minigames, so it never covers the game's own UI.

The full reasoning is in [`docs/controls.md`](docs/controls.md).

---

## Building

The Android build needs the Android NDK, CMake and Gradle, which is a heavy
dependency tree. It is set up to run on GitHub Actions, so a plain push is
enough:

```bash
git push origin main
```

Then grab the APK from the **Actions** tab, or from the **Releases** page if
you pushed a `V*` tag.

### Building locally instead

```bash
# 1. Get the Butterscotch runner this port is based on
git clone --depth 1 https://github.com/ButterscotchRunner/Butterscotch.git vendor/Butterscotch

# 2. Apply the port patches
python3 scripts/apply_port.py vendor/Butterscotch
python3 scripts/apply_game_screen.py vendor/Butterscotch

# 3. Build
cd vendor/Butterscotch/src/android/frontend
./gradlew :app:assembleRelease

# The APK lands in app/build/outputs/apk/release/
```

Requirements: JDK 17, Android SDK with platform 36, build-tools 35.0.0,
NDK 27.0.12077973 and CMake 3.22.1.

---

## Getting the game onto your phone

The APK is just the runner — the game files are **not** redistributed here,
because they belong to SpookyRick. Get *Five Nights at Frickbear's 3* v1.1.4
from [Game Jolt](https://gamejolt.com/games/frickbears3/930477) and unpack it
so you have a folder containing:

```
data.win
audiogroup1.dat ... audiogroup7.dat
texgroup_buildingtextures/*.yytex
texgroup_conceptart/*.yytex
...
leveldata1.txt ... leveldata5.txt
options.ini
```

Then in the app: **Import** → pick that folder → the game shows up in your
library → launch it. The Butterscotch importer recognises `data.win` (and
also `game.unx` / `game.droid` if you have a different export).

If you want the files without going through Game Jolt's download flow, a few
community character mods on itch.io bundle the full base game:

```bash
# Downloads a mirror that contains the full data.win and unpacks it
python3 tools/fetch_game.py
```

This writes to `vendor/frickbears3-game/`. It is a convenience only — the
canonical source is Game Jolt.

---

## Repository layout

```
.
├── app/                          the Kotlin touch overlay
│   ├── FrickBears3TouchOverlay.kt    the on-screen buttons
│   ├── Fb3Keys.kt                    default key bindings + overlay visibility policy
│   └── Fb3CameraSwipe.kt             swipe-to-change-camera
├── layouts/                      the FB3 touch layout (Butterscotch layout JSON)
├── scripts/
│   ├── apply_port.py             applies the port patches to a Butterscotch checkout
│   └── apply_game_screen.py      wires the overlay into the game screen
├── docs/controls.md              the control design rationale
├── .github/workflows/            the APK build
└── tools/                        helpers for inspecting the game's data.win
```

### Tools

`tools/` contains small Python helpers for looking inside the game's
`data.win`, which is a GameMaker "FORM" container:

```bash
python3 tools/dump_strg.py path/to/data.win       # dump the string table
python3 tools/find_controls.py path/to/data.win   # find the control definitions
python3 tools/list_rooms.py path/to/data.win      # list the game's rooms
```

---

## Credits

- **Five Nights at Frickbear's 3** — SpookyRick. The original game, and all of
  its art, audio and code.
- **[Butterscotch](https://github.com/ButterscotchRunner/Butterscotch)** —
  the open-source GameMaker runner this port is built on, by the Butterscotch
  contributors. AGPL-3.0.
- The community Android ports of FB3 by
  [@JOTE_](https://gamejolt.com/@JOTE_) and
  [@Foxyexe143](https://gamejolt.com/@Foxyexe143), whose touch-control design
  work set the direction for this overlay.
- [@Fredkz](https://gamejolt.com/@Fredkz) for the earlier FB3 mobile port.

## Licence

The port code in this repository is AGPL-3.0, matching Butterscotch. The game files
are not part of this repository and remain the property of SpookyRick. See
[`GAME_FILES.md`](GAME_FILES.md).
