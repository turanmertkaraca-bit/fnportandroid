#!/usr/bin/env python3
"""Wire the FrickBears 3 touch overlay into Butterscotch's game screen.

This is the part of the port that actually makes the game playable on a phone:

  * adds the overlay composable on top of the game surface,
  * feeds it the runner's current room name so it can hide itself outside the
    night shift,
  * routes its key presses into the same input queue the physical keyboard
    uses, so the game sees ordinary GML key events,
  * tracks whether the monitor is up, so the camera swipe only fires while the
    camera panel is actually on screen,
  * routes the camera swipe into synthetic mouse clicks on the game's own
    camera tabs.

Usage:  python3 apply_game_screen.py <butterscotch-checkout>
"""
import os
import sys

OK, SKIP, FAIL = "ok", "skip", "fail"


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def sub(path, anchor, replacement, marker):
    """Replace `anchor` with `replacement`. Idempotent via `marker`."""
    if not os.path.exists(path):
        return FAIL, f"missing {path}"
    text = read(path)
    if marker in text:
        return SKIP, "already applied"
    if anchor not in text:
        return FAIL, "anchor not found"
    write(path, text.replace(anchor, replacement, 1))
    return OK, "applied"


def main():
    if len(sys.argv) < 2:
        print("usage: apply_game_screen.py <butterscotch-checkout>")
        return 2
    root = sys.argv[1]

    activity = os.path.join(
        root,
        "src/android/frontend/app/src/main/kotlin/net/perfectdreams/butterscotch/android/GameActivity.kt",
    )

    results = []

    # --- 1. Imports ----------------------------------------------------------
    results.append(("imports",) + sub(
        activity,
        "import net.perfectdreams.butterscotch.android.layouts.GamepadElement\n",
        "import net.perfectdreams.butterscotch.android.frickbears3.Fb3Keys\n"
        "import net.perfectdreams.butterscotch.android.frickbears3.Fb3OverlayPolicy\n"
        "import net.perfectdreams.butterscotch.android.frickbears3.FrickBears3TouchOverlay\n"
        "import net.perfectdreams.butterscotch.android.frickbears3.rememberFb3CameraSwiper\n"
        "import net.perfectdreams.butterscotch.android.layouts.GamepadElement\n",
        "import net.perfectdreams.butterscotch.android.frickbears3.Fb3Keys",
    ))

    results.append(("coroutines import",) + sub(
        activity,
        "import androidx.compose.runtime.getValue\n",
        "import androidx.compose.runtime.getValue\nimport kotlinx.coroutines.delay\n",
        "import kotlinx.coroutines.delay\n",
    ))

    # --- 2. Room + monitor state --------------------------------------------
    # The room name decides whether the overlay is shown at all; the monitor
    # flag decides whether a camera swipe should do anything.
    results.append(("room + monitor state",) + sub(
        activity,
        "                        val isPortrait = constraints.maxHeight >= constraints.maxWidth\n",
        "                        val isPortrait = constraints.maxHeight >= constraints.maxWidth\n"
        "\n"
        "                        // ===[ FrickBears 3 port ]===\n"
        "                        // The FB3 touch overlay shows itself only during the night\n"
        "                        // shift, so we poll the runner for the current room name.\n"
        "                        var fb3RoomName by remember { mutableStateOf<String?>(null) }\n"
        "                        LaunchedEffect(Unit) {\n"
        "                            while (true) {\n"
        "                                val name = ButterscotchNative.getCurrentRoomName()\n"
        "                                if (name != fb3RoomName) fb3RoomName = name\n"
        "                                delay(500)\n"
        "                            }\n"
        "                        }\n"
        "                        val fb3OverlayVisible = Fb3OverlayPolicy.shouldShow(fb3RoomName)\n"
        "\n"
        "                        // The camera swipe only makes sense while the monitor is on\n"
        "                        // screen. FB3 raises the monitor with the W key by default, so\n"
        "                        // we mirror that here.\n"
        "                        var fb3MonitorUp by remember { mutableStateOf(false) }\n",
        "var fb3RoomName by remember",
    ))

    # --- 3. Camera swiper ----------------------------------------------------
    results.append(("camera swiper",) + sub(
        activity,
        "                        var fb3MonitorUp by remember { mutableStateOf(false) }\n",
        "                        var fb3MonitorUp by remember { mutableStateOf(false) }\n"
        "\n"
        "                        // The swipe turns into clicks on the game's own camera tab\n"
        "                        // strip, so it works no matter how the monitor is laid out or\n"
        "                        // which tabs are unlocked.\n"
        "                        val fb3CameraSwiper = rememberFb3CameraSwiper(\n"
        "                            isMonitorUp = { fb3MonitorUp },\n"
        "                            clickAt = { nx, ny ->\n"
        "                                butterscotchRunner.onMouseMove(nx, ny)\n"
        "                                butterscotchRunner.onMouseButton(GmlMouseButton.LEFT_BUTTON, true)\n"
        "                                butterscotchRunner.onMouseButton(GmlMouseButton.LEFT_BUTTON, false)\n"
        "                            },\n"
        "                        )\n",
        "rememberFb3CameraSwiper(",
    ))

    # --- 4. The overlay itself ------------------------------------------------
    results.append(("overlay composable",) + sub(
        activity,
        "                            LayoutMode.Overlay -> {\n"
        "                                Box(Modifier.fillMaxSize()) {\n"
        "                                    gameSurface(Modifier.fillMaxSize())\n",
        "                            LayoutMode.Overlay -> {\n"
        "                                Box(Modifier.fillMaxSize()) {\n"
        "                                    gameSurface(Modifier.fillMaxSize())\n"
        "\n"
        "                                    // ===[ FrickBears 3 port ]===\n"
        "                                    // The FB3 touch overlay: the four\n"
        "                                    // high-frequency night actions in the\n"
        "                                    // thumb zone, plus swipe-to-change-camera.\n"
        "                                    if (!freeCam.active && fb3OverlayVisible) {\n"
        "                                        FrickBears3TouchOverlay(\n"
        "                                            enabled = true,\n"
        "                                            haptics = { performHaptic() },\n"
        "                                            onKeyPress = { vk ->\n"
        "                                                if (vk == Fb3Keys.VK_MONITOR) {\n"
        "                                                    fb3MonitorUp = !fb3MonitorUp\n"
        "                                                }\n"
        "                                                butterscotchRunner.onKey(vk, true)\n"
        "                                            },\n"
        "                                            onKeyRelease = { vk ->\n"
        "                                                butterscotchRunner.onKey(vk, false)\n"
        "                                            },\n"
        "                                            onSwipeCamera = { direction ->\n"
        "                                                fb3CameraSwiper.step(direction)\n"
        "                                            },\n"
        "                                            modifier = Modifier.fillMaxSize(),\n"
        "                                        )\n"
        "                                    }\n",
        "FrickBears3TouchOverlay(",
    ))

    failed = 0
    for name, status, detail in results:
        print(f"  {status:4}  {name:22} {detail}")
        if status == FAIL:
            failed += 1

    print()
    if failed:
        print(f"{failed} step(s) FAILED")
        return 1
    print("game screen wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
