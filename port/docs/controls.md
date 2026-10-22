# FB3 Android Port — Control Mapping

## How FB3's controls work (verified against the shipped `data.win`)

FB3 (`Five Nights at Frickbear's 3`, GameMaker: Studio 2.3, v1.1.4) is a
point-and-click night-guard game. The night loop is:

1. Watch the **monitor** to see where animatronics are.
2. **Flashlight** the hallways to check whether something is there.
3. **Close the Left Door / Right Door** to block an animatronic that reached
   the office doorway. Doors consume power.
4. **Fan** to control the temperature; the fan also consumes power.
5. Optional: the **Vents** monitor tab, the **Reset Music** button on the
   entrance camera, and a **spare Freddy mask**.

All of these are **click targets in the game world**, not separate keys. The
game exposes a "Controls Options" screen (`ControlsOptions` /
`remapFunction` / `controlslist` in the string table) that lets the player
rebind keyboard and mouse input, and the control names in the binary are:

```
Left Door
Right Door
Flashlight
Monitor
PreviousCamera
The Fan
Reset Music
Laser Doors
Vents
```

The game also ships these helper functions, which show the same surface:
`gml_Script_disable_camera`, `gml_Script_disable_flashlight`,
`gml_Script_disable_doors`, `gml_Script_disable_fan`.

## Implication for the port

Because the game is click-driven, the most faithful touch port is:

- **A transparent overlay that taps the real game UI**, not a set of fake
  buttons that emulate keys. This keeps every interaction working (menus,
  minigames, the salvage rooms) without needing to know the game's internals.
- **A small set of *accelerator* buttons** in the thumb zone for the actions
  that must be hit repeatedly under pressure: the two doors and the flashlight.

This is the hybrid the JOTE_/Foxyexe143 community port used, and it is the
reason that port feels good: the overlay is unobtrusive, but the high-frequency
actions are one thumb-tap away.

## The accelerator buttons

Butterscotch's overlay can inject **GML keyboard vk codes** (`InputBinding.Keyboard`)
or **mouse buttons** (`GamepadElement.MouseButton`). FB3 remaps its controls
from the in-game options screen, so the port ships a *default* binding that the
player can re-map inside the game itself, plus the overlay's own re-bindable
layout.

| Overlay button | Default binding | Purpose |
| --- | --- | --- |
| `L. DOOR` | `A` (vk 65) | Toggle the left door |
| `R. DOOR` | `D` (vk 68) | Toggle the right door |
| `LIGHT` | `S` (vk 83) | Toggle the flashlight |
| `MONITOR` | `W` (vk 87) | Raise / lower the monitor |

> These are defaults, not hard requirements. FB3's own options screen is the
> source of truth; if a player rebinds a key there, they rebind the overlay
> button to match (or vice-versa) in the layout editor.

## Feel requirements ("you need to flow through it")

FB3 is a hard game. The port therefore optimises for *flow*:

1. **Fire on press, not release.** Every button in the overlay fires the
   instant the finger lands. A release-triggered button costs ~80 ms of
   perceived latency per action and feels mushy when you are panicking.
2. **No sliding cancels.** A finger that drifts off a button still triggers it.
   The player is often sliding a thumb across the screen under stress; making
   that a cancel would silently drop a door.
3. **Toggle, not hold.** Doors and the monitor are *latched* actions in the
   game. A hold-to-activate button would require the finger to stay down for
   the whole time a door is shut, which is both tiring and easy to lose.
   The overlay buttons are therefore one-tap toggles.
4. **Everything in the thumb zone.** Buttons sit in the bottom band
   (`positionY ≈ 0.78`) and are sized as a fraction of the shorter viewport
   edge, so they scale correctly from a small phone to a tablet.
5. **Swipe to change camera.** The in-game monitor has several tabs
   (entrance, dining, kitchen, …, plus Vents). Reaching for a tab in the
   monitor UI is slow. The port adds a horizontal swipe across the game
   surface that steps the camera tab, so switching cameras is a flick rather
   than a hunt.
6. **Haptics on every action.** A short pulse confirms the press without
   looking at the screen — essential when the eyes are on the monitor.

## Screens where the overlay is hidden

The overlay is a *night* aid. It is hidden on:

- the title screen,
- the salvage / maze rooms (these are 3D free-roam and need direct touch),
- the minigames (these are mouse-driven microgames),
- the shop and extras.

The port detects these from the room name reported by the runner
(`ButterscotchNative.getCurrentRoomName()`), so the overlay never fights with
the game's own UI.
