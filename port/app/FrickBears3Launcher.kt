package net.perfectdreams.butterscotch.android.frickbears3

import android.content.Context
import android.content.Intent
import android.util.Log
import net.perfectdreams.butterscotch.android.GameActivity
import net.perfectdreams.butterscotch.android.library.GameLibrary
import java.io.File

/**
 * The FrickBears 3 app's start-up path.
 *
 * The app is a purpose-built runner for one game, so it does not show a
 * launcher with a game list: it installs the bundled game (see
 * [BundledGame]) and opens it straight away. Everything the generic
 * Butterscotch launcher offered - importing other games, browsing a
 * library, the store - is irrelevant here and only got in the way.
 *
 * If the bundled game somehow cannot be installed, the app falls back to the
 * regular launcher rather than showing a dead screen, so the player can still
 * import the game by hand.
 */
object FrickBears3Launcher {
    private const val TAG = "FrickBears3Launcher"

    /**
     * Installs the bundled game and returns the intent that opens it.
     *
     * @return an intent for [GameActivity], or null when the bundled game is
     *         not available and the normal launcher should be shown.
     */
    fun prepareGameLaunch(context: Context, gameLibrary: GameLibrary): Intent? {
        val entry = BundledGame.installIfNeeded(context, gameLibrary)
        if (entry == null) {
            Log.w(TAG, "The bundled game is unavailable; falling back to the launcher")
            return null
        }

        return Intent(context, GameActivity::class.java).apply {
            putExtra(GameActivity.EXTRA_GAME_ID, entry.id.toString())
            addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION)
        }
    }

    /**
     * True when the bundled game is present and registered.
     */
    fun isGameReady(context: Context, gameLibrary: GameLibrary): Boolean {
        val entry = gameLibrary.findById(BundledGame.GAME_ID) ?: return false
        val wad = gameLibrary.wadPath(entry)
        return wad.exists() && wad.length() > 0
    }
}
