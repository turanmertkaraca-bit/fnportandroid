#!/usr/bin/env python3
"""Apply the FrickBears 3 port patches to a Butterscotch checkout.

The patches are deliberately small and additive:

  1. A native accessor for the *current* room name / index, so the Kotlin
     touch overlay can decide whether to show itself.
  2. Kotlin declarations for that accessor.
  3. The FrickBears 3 touch overlay composable, its key bindings and the
     camera swipe helper.
  4. The FB3 landscape layout, registered as a built-in layout.

The game-screen wiring lives in apply_game_screen.py and runs right after this.

Everything is applied as text substitution with a marker check, so re-running
the script on an already-patched tree is a no-op instead of a failure.

Usage:  python3 apply_port.py <butterscotch-checkout>
"""
import os
import sys

OK = "ok"
SKIP = "skip"
FAIL = "fail"


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def substitute(path, anchor, addition, marker, mode="after"):
    """Insert `addition` relative to `anchor`. Idempotent via `marker`."""
    if not os.path.exists(path):
        return FAIL, f"missing {path}"
    text = read(path)
    if marker in text:
        return SKIP, "already applied"
    if anchor not in text:
        return FAIL, f"anchor not found in {path}"
    if mode == "after":
        text = text.replace(anchor, anchor + addition, 1)
    else:
        text = text.replace(anchor, addition + anchor, 1)
    write(path, text)
    return OK, "applied"


def copy_file(src, dst):
    if os.path.exists(dst):
        return SKIP, "already present"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, "rb") as a, open(dst, "wb") as b:
        b.write(a.read())
    return OK, "copied"


def main():
    if len(sys.argv) < 2:
        print("usage: apply_port.py <butterscotch-checkout>")
        return 2

    root = sys.argv[1]
    port_dir = os.path.dirname(os.path.abspath(__file__))
    port_dir = os.path.dirname(port_dir)  # .../port

    results = []

    # --- 1. Native: current room name/index ---------------------------------
    native_main = os.path.join(root, "src/android/main.c")
    native_addition = """
// ===[ FrickBears 3 port additions ]===

// The Android touch overlay needs to know which room the game is in so it can
// hide itself outside the night shift. Butterscotch exposes getRoomCount() and
// getRoomName(index), but there is no way to ask "what room am I in right
// now", so these two accessors fill that gap.

JNIEXPORT jint JNICALL JNI_FN(getCurrentRoomIndex)(MAYBE_UNUSED JNIEnv* env, MAYBE_UNUSED jclass cls) {
    Runner* runner = gRunner;
    if (runner == nullptr) return -1;
    return runner->currentRoomIndex;
}

JNIEXPORT jstring JNICALL JNI_FN(getCurrentRoomName)(MAYBE_UNUSED JNIEnv* env, MAYBE_UNUSED jclass cls) {
    Runner* runner = gRunner;
    if (runner == nullptr || runner->currentRoom == nullptr) return NULL;

    const char* name = runner->currentRoom->name;
    if (name == NULL) return NULL;

    return (*env)->NewStringUTF(env, name);
}
"""
    results.append(("native/main.c",) + substitute(
        native_main,
        "JNIEXPORT jint JNICALL JNI_FN(getRoomCount)",
        native_addition,
        "getCurrentRoomName",
        mode="before",
    ))

    # --- 2. Kotlin: native declarations -------------------------------------
    native_kt = os.path.join(
        root,
        "src/android/frontend/app/src/main/kotlin/net/perfectdreams/butterscotch/android/ButterscotchNative.kt",
    )
    kt_addition = """
    // ===[ FrickBears 3 port additions ]===

    /**
     * Index of the room the game is currently in, or -1 if there is none.
     * Lets the touch overlay decide whether to show itself.
     */
    external fun getCurrentRoomIndex(): Int

    /** Name of the room the game is currently in, or null if there is none. */
    external fun getCurrentRoomName(): String?
"""
    results.append(("ButterscotchNative.kt",) + substitute(
        native_kt,
        "    // ===[ Native -> Kotlin push state ]===",
        kt_addition,
        "getCurrentRoomName",
        mode="before",
    ))

    # --- 3. Overlay sources --------------------------------------------------
    kt_dir = os.path.join(
        root,
        "src/android/frontend/app/src/main/kotlin/net/perfectdreams/butterscotch/android/frickbears3",
    )
    for name in ("FrickBears3TouchOverlay.kt", "Fb3Keys.kt", "Fb3CameraSwipe.kt"):
        results.append((f"frickbears3/{name}",) + copy_file(
            os.path.join(port_dir, "app", name),
            os.path.join(kt_dir, name),
        ))

    # --- 4. The FB3 layout as a built-in layout ------------------------------
    layouts_dir = os.path.join(
        root, "src/android/frontend/app/src/main/assets/layouts"
    )
    results.append(("assets/layouts/frickbears3.json",) + copy_file(
        os.path.join(port_dir, "layouts", "frickbears3_touch_landscape.json"),
        os.path.join(layouts_dir, "frickbears3.json"),
    ))

    failed = 0
    for name, status, detail in results:
        print(f"  {status:4}  {name:42} {detail}")
        if status == FAIL:
            failed += 1

    print()
    if failed:
        print(f"{failed} step(s) FAILED")
        return 1
    print("all steps applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
