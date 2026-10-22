package net.perfectdreams.butterscotch.android.frickbears3

/**
 * Default key bindings for the FrickBears 3 touch overlay.
 *
 * These are the GML virtual-key codes the runner forwards to the game
 * (`ButterscotchNative.onKeyDown` / `onKeyUp`). FB3 has its own in-game
 * "Controls Options" screen that remaps keyboard and mouse input, so these
 * are only the *defaults* - a player who rebinds "Left Door" to another key
 * should rebind the overlay button to match.
 *
 * The defaults are chosen to be:
 *  - on the home row (easy to hit without looking),
 *  - spread across both hands (left hand = light + left door, right hand =
 *    right door + monitor),
 *  - far from keys the game might also use for menu navigation (arrows, Enter,
 *    Escape), so a stray overlay press cannot open a menu mid-night.
 */
object Fb3Keys {
    /** Flashlight toggle. */
    const val VK_FLASHLIGHT = 83 // S

    /** Left door toggle. */
    const val VK_LEFT_DOOR = 65 // A

    /** Right door toggle. */
    const val VK_RIGHT_DOOR = 68 // D

    /** Monitor (camera panel) toggle. */
    const val VK_MONITOR = 87 // W
}

/**
 * Decides when the FrickBears 3 overlay should be visible.
 *
 * The overlay is a *night* aid. Outside the night shift it would sit on top
 * of the title screen, the shop, the salvage maze and the minigames, where it
 * would either cover important UI or fight with the game's own touch handling.
 *
 * The runner reports the current room name (`ButterscotchNative.getCurrentRoomName`),
 * so the overlay keys off the room rather than trying to guess from a
 * screenshot.
 */
object Fb3OverlayPolicy {
    /**
     * Substrings of room names where the overlay must stay hidden.
     *
     * These cover the title screen, the hub, the shop, the extras gallery, the
     * 3D free-roam salvage locations and the microgames. Anything that is not
     * a plain night room falls into the hidden bucket, which is the safe
     * default: a missing overlay button is an annoyance, an overlay sitting
     * on top of the salvage maze is a broken game.
     */
    private val HIDDEN_ROOM_MARKERS = listOf(
        "title",
        "menu",
        "shop",
        "extras",
        "gallery",
        "salvage",
        "maze",
        "microgame",
        "minigame",
        "credits",
        "options",
        "customnight",
        "boss",
        "end",
        "intro",
        "loading",
    )

    /**
     * @param roomName the current room's name, or null if it cannot be read.
     * @return true when the overlay should be shown.
     */
    fun shouldShow(roomName: String?): Boolean {
        if (roomName.isNullOrBlank()) return false

        val normalized = roomName.lowercase().replace("_", "").replace(" ", "")

        // A night room is the only place the overlay makes sense. The game's
        // night rooms are named after the location plus the night, e.g.
        // "room_night1_pizzeria" or similar; we detect them by the presence
        // of a night marker, and treat everything else as hidden.
        val looksLikeNight = normalized.contains("night") ||
            normalized.contains("office") ||
            normalized.contains("guard")

        if (!looksLikeNight) return false

        return HIDDEN_ROOM_MARKERS.none { normalized.contains(it) }
    }
}
