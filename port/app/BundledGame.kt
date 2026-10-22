package net.perfectdreams.butterscotch.android.frickbears3

import android.content.Context
import android.util.Log
import net.perfectdreams.butterscotch.android.layouts.LayoutLibrary
import net.perfectdreams.butterscotch.android.library.GameEntry
import net.perfectdreams.butterscotch.android.library.GameLibrary
import java.io.File
import java.util.UUID
import java.util.zip.ZipInputStream

/**
 * Installs the FrickBears 3 game that ships inside the APK.
 *
 * The game's data (data.win, the audio groups and the texture groups) is
 * bundled as a compressed archive in the APK's assets, because it is far too
 * large to ship as loose files. On first launch it is extracted into the
 * app's private storage and registered in the game library, so the game
 * appears in the launcher without the player having to import anything.
 *
 * The extraction is idempotent: a marker file records the version of the
 * archive that was installed, and a re-install only happens when the bundled
 * data changes.
 */
object BundledGame {
    private const val TAG = "BundledGame"

    /** Where the compressed game lives inside the APK. */
    private const val ASSET_PATH = "game/frickbears3.zip"

    /** Bumped whenever the bundled data changes, to force a re-extract. */
    private const val BUNDLE_VERSION = 1

    /** Fixed id, so the game keeps the same library entry across re-installs. */
    val GAME_ID: UUID = UUID.fromString("f1c9b3a4-5d2e-4f60-9a71-8c3b2e6d5a90")

    const val TITLE = "Five Nights at Frickbear's 3"

    /**
     * The id of the FB3 touch layout, registered by [LayoutLibrary] when the
     * app starts. The game is assigned it so the touch controls are active
     * out of the box.
     */
    val TOUCH_LAYOUT_ID: UUID = UUID.fromString("a1f4c2d8-3b7e-4c91-8f26-5d0e7b3a9c14")

    private const val INSTALLED_MARKER = "bundled_installed_version"

    /**
     * Extracts the bundled game (if needed) and makes sure it is registered in
     * the library.
     *
     * @return the library entry for the game, or null if it could not be
     *         installed (in which case the player can still import it
     *         manually).
     */
    fun installIfNeeded(context: Context, gameLibrary: GameLibrary): GameEntry? {
        val alreadyInstalled = gameLibrary.findById(GAME_ID)
        if (alreadyInstalled != null && isUpToDate(context)) {
            Log.i(TAG, "Bundled game already installed")
            return alreadyInstalled
        }

        return try {
            // The library owns the per-game directory layout, so the files are
            // written where the runner expects to find them.
            val gameDir = gameLibrary.gameDir(GAME_ID)
            val bundleDir = File(gameDir, "bundle")
            File(gameDir, "saves").mkdirs()
            File(gameDir, "logs").mkdirs()

            installInto(context, bundleDir)
            register(context, gameLibrary, bundleDir)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to install the bundled game", e)
            null
        }
    }

    /**
     * Unpacks the archive into [targetDir].
     */
    private fun installInto(context: Context, targetDir: File) {
        targetDir.mkdirs()

        val asset = context.assets.open(ASSET_PATH)
        ZipInputStream(asset.buffered()).use { zip ->
            var entry = zip.nextEntry
            while (entry != null) {
                // Guard against path traversal in the archive.
                val name = entry.name.replace('\\', '/')
                if (name.contains("..")) {
                    Log.w(TAG, "Skipping suspicious entry $name")
                    zip.closeEntry()
                    entry = zip.nextEntry
                    continue
                }

                val outFile = File(targetDir, name)
                if (entry.isDirectory) {
                    outFile.mkdirs()
                } else {
                    outFile.parentFile?.mkdirs()
                    outFile.outputStream().use { output ->
                        zip.copyTo(output)
                    }
                }
                zip.closeEntry()
                entry = zip.nextEntry
            }
        }
        Log.i(TAG, "Extracted the bundled game to $targetDir")
    }

    /**
     * Adds the freshly extracted game to the library.
     */
    private fun register(
        context: Context,
        gameLibrary: GameLibrary,
        bundleDir: File,
    ): GameEntry? {
        // The staged directory is where the importer would normally put the
        // files; we reuse the one we just filled.
        val staged = GameLibrary.StagedGame(
            GAME_ID,
            bundleDir,
            File(bundleDir.parentFile, "saves"),
        )

        // Replace any previous entry for this id so a re-install does not
        // leave a stale one behind.
        gameLibrary.findById(GAME_ID)?.let { gameLibrary.remove(it.id) }

        gameLibrary.commit(
            staged = staged,
            title = TITLE,
            gameType = GameEntry.GameType.GameMakerStudio(
                wadVersion = 17,
                filename = "data.win",
            ),
            portraitLayout = TOUCH_LAYOUT_ID,
            landscapeLayout = TOUCH_LAYOUT_ID,
            // Report as Android so the game picks its mobile code paths, and
            // turn the physical controller off - FB3 does not use a gamepad
            // and a connected controller can confuse its input handling.
            runnerOs = GameEntry.RunnerOs.ANDROID,
            enablePhysicalControllers = false,
            enablePhysicalKeyboard = true,
        )

        context.getSharedPreferences("frickbears3", Context.MODE_PRIVATE)
            .edit()
            .putInt(INSTALLED_MARKER, BUNDLE_VERSION)
            .apply()

        Log.i(TAG, "Registered the bundled game")
        return gameLibrary.findById(GAME_ID)
    }

    private fun isUpToDate(context: Context): Boolean {
        val prefs = context.getSharedPreferences("frickbears3", Context.MODE_PRIVATE)
        return prefs.getInt(INSTALLED_MARKER, 0) == BUNDLE_VERSION
    }
}
