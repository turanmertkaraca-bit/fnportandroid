#!/usr/bin/env python3
"""Turn the Butterscotch app into a dedicated FrickBears 3 runner.

Butterscotch is a general-purpose GameMaker runner: it shows a launcher, lets
you import other games, and has store, ads and Play Services update plumbing.
None of that is wanted for a single-game port, and the launcher in particular
means the app does not open the game - the player has to tap through a list
first.

This script rewrites the app's entry points so that:

  * the bundled game is installed and registered on first launch,
  * the app opens straight into the game,
  * the Play Services update plumbing is dropped (it is dead weight without
    a Play Store listing, and it is the only reason the app needs the
    com.google.android.play dependency).

Usage:  python3 apply_trim.py <butterscotch-checkout>
"""
import os
import sys

OK, SKIP, FAIL = "ok", "skip", "fail"

APP = "src/android/frontend/app"
KT = "src/android/frontend/app/src/main/kotlin/net/perfectdreams/butterscotch/android"


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def sub(path, anchor, replacement, marker):
    if not os.path.exists(path):
        return FAIL, f"missing {path}"
    text = read(path)
    if marker in text:
        return SKIP, "already applied"
    if anchor not in text:
        return FAIL, "anchor not found"
    write(path, text.replace(anchor, replacement, 1))
    return OK, "applied"


MAIN_ACTIVITY = '''package net.perfectdreams.butterscotch.android

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import net.perfectdreams.butterscotch.android.frickbears3.FrickBears3Launcher
import net.perfectdreams.butterscotch.android.theme.ButterscotchAndroidTheme
import java.util.UUID

/**
 * The FrickBears 3 runner's entry point.
 *
 * Unlike the upstream Butterscotch app, this does not show a launcher with a
 * list of games. The game is bundled in the APK, so the app installs it on
 * first launch and opens it straight away.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)

        val gameLibrary = Libraries.loadGameLibrary(this.applicationContext)
        val layoutLibrary = Libraries.loadLayoutLibrary(this.applicationContext)
        val settingsStore = Libraries.loadSettingsStore(this.applicationContext)

        // Already inside the game (a "play" intent from the launcher, or a
        // re-create after a configuration change) - just hand over.
        if (intent?.action == ACTION_LAUNCH_GAME) {
            val gameIdAsString = intent.getStringExtra(GameActivity.EXTRA_GAME_ID)
            intent.action = null
            intent.removeExtra(GameActivity.EXTRA_GAME_ID)
            if (gameIdAsString != null) {
                val gameId = UUID.fromString(gameIdAsString)
                if (gameLibrary.findById(gameId) != null) {
                    startActivity(Intent(this, GameActivity::class.java).apply {
                        putExtra(GameActivity.EXTRA_GAME_ID, gameId.toString())
                    })
                    finish()
                    return
                }
            }
        }

        // Install the bundled game and open it. If that is not possible we
        // fall back to the normal launcher so the player can import the game
        // by hand instead of staring at a blank screen.
        val gameIntent = FrickBears3Launcher.prepareGameLaunch(this, gameLibrary)
        if (gameIntent != null) {
            startActivity(gameIntent)
            finish()
            return
        }

        enableEdgeToEdge(
            navigationBarStyle = SystemBarStyle.dark(
                scrim = android.graphics.Color.TRANSPARENT
            )
        )

        setContent {
            ButterscotchAndroidTheme {
                var splashGone by rememberSaveable { mutableStateOf(false) }
                Box(Modifier.fillMaxSize()) {
                    ButterscotchApp(gameLibrary, layoutLibrary, settingsStore, null)
                    if (!splashGone) {
                        SplashReveal(onFinished = { splashGone = true })
                    }
                }
            }
        }
    }

    companion object {
        const val ACTION_LAUNCH_GAME = "net.perfectdreams.butterscotch.android.action.LAUNCH_GAME"
    }
}
'''


def main():
    if len(sys.argv) < 2:
        print("usage: apply_trim.py <butterscotch-checkout>")
        return 2
    root = sys.argv[1]

    results = []

    # --- 1. MainActivity: launch the game directly --------------------------
    main_activity = os.path.join(root, KT, "MainActivity.kt")
    if not os.path.exists(main_activity):
        print(f"  FAIL  MainActivity.kt missing")
        return 1

    text = read(main_activity)
    if "FrickBears3Launcher" in text:
        results.append(("MainActivity.kt", SKIP, "already applied"))
    else:
        write(main_activity, MAIN_ACTIVITY)
        results.append(("MainActivity.kt", OK, "rewritten"))

    # --- 2. Drop the Play Services update dependency ------------------------
    # app-update is only useful for a Play Store listing, and pulling in the
    # Play Services library for a fan port is pointless weight.
    build_gradle = os.path.join(root, APP, "build.gradle.kts")
    results.append(("build.gradle.kts",) + sub(
        build_gradle,
        '    implementation("com.google.android.play:app-update:2.1.0")\n'
        '    implementation("com.google.android.play:app-update-ktx:2.1.0")\n',
        "    // FrickBears 3 port: the Play Services update flow is not used.\n",
        "FrickBears 3 port: the Play Services update flow is not used.",
    ))

    # --- 3. Rename the app -------------------------------------------------
    strings = os.path.join(
        root, APP, "src/main/res/values/strings.xml"
    )
    if os.path.exists(strings):
        content = read(strings)
        content = content.replace(
            "<string name=\"app_name\">Butterscotch</string>",
            "<string name=\"app_name\">FrickBears 3</string>",
        )
        write(strings, content)
        results.append(("strings.xml", OK, "renamed"))
    else:
        results.append(("strings.xml", FAIL, "missing"))

    manifest = os.path.join(root, APP, "src/main/AndroidManifest.xml")
    if os.path.exists(manifest):
        content = read(manifest)
        # The app is not distributed through the Play Store, so the ad id and
        # the Play Services application id are dead weight.
        content = content.replace(
            '    <uses-permission android:name="com.google.android.gms.permission.AD_ID" />\n',
            "",
        )
        content = content.replace(
            "        <!-- AdMob App ID -->\n"
            "        <meta-data\n"
            '            android:name="com.google.android.gms.ads.APPLICATION_ID"\n'
            '            android:value="ca-app-pub-9989170954243288~7593266164" />\n\n',
            "",
        )
        write(manifest, content)
        results.append(("AndroidManifest.xml", OK, "cleaned"))
    else:
        results.append(("AndroidManifest.xml", FAIL, "missing"))

    failed = 0
    for name, status, detail in results:
        print(f"  {status:4}  {name:28} {detail}")
        if status == FAIL:
            failed += 1

    print()
    if failed:
        print(f"{failed} step(s) FAILED")
        return 1
    print("app trimmed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
