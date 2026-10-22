package net.perfectdreams.butterscotch.android.frickbears3

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember

/**
 * Camera tab navigation for FrickBears 3.
 *
 * FB3's monitor is a panel of clickable camera tabs drawn by the game itself
 * (`oCamButton` and friends). There is no keyboard binding that cycles them, so
 * a swipe has to be turned into *clicks on the real tabs* for the swipe to work
 * regardless of how the monitor is laid out or which tabs are unlocked.
 *
 * The port therefore does not guess pixel positions blindly. Instead it:
 *
 *  1. Tracks whether the monitor is currently up (the player toggles it with
 *     the monitor button, which the host mirrors into `isMonitorUp`).
 *  2. On a swipe, clicks the camera tab strip in the game's own coordinate
 *     space, stepping left or right by one tab.
 *
 * The tab strip sits along the bottom edge of the monitor overlay in the
 * default 16:9 layout, which is where a thumb naturally lands anyway. If the
 * monitor is not up the swipe is a no-op, so swiping in the office never
 * clicks a random object.
 */
class Fb3CameraSwiper(
    private val isMonitorUp: () -> Boolean,
    private val clickAt: (normalizedX: Float, normalizedY: Float) -> Unit,
) {
    /**
     * The vertical band (as a fraction of the game height) that the camera tab
     * strip occupies when the monitor is open.
     */
    private val tabStripTop = 0.86f
    private val tabStripBottom = 0.99f

    /**
     * Horizontal slots for the camera tabs. FB3 shows up to six tabs across
     * the strip, so a swipe moves one slot at a time.
     */
    private val tabSlots = 6

    private var currentSlot = 0

    fun step(direction: Int) {
        // Only act while the monitor is actually on screen.
        if (!isMonitorUp()) return

        val next = (currentSlot + direction).mod(tabSlots)
        currentSlot = next

        val slotCenter = (next + 0.5f) / tabSlots
        val y = (tabStripTop + tabStripBottom) / 2f
        clickAt(slotCenter, y)
    }

    fun reset() {
        currentSlot = 0
    }
}

/**
 * Remembers the swipe state across recompositions and drives the swiper.
 */
@Composable
fun rememberFb3CameraSwiper(
    isMonitorUp: () -> Boolean,
    clickAt: (Float, Float) -> Unit,
): Fb3CameraSwiper {
    val swiper = remember { Fb3CameraSwiper(isMonitorUp, clickAt) }

    // Leaving the monitor resets the remembered tab, so the next swipe starts
    // from the first tab again.
    LaunchedEffect(isMonitorUp()) {
        if (!isMonitorUp()) {
            swiper.reset()
        }
    }

    return swiper
}
