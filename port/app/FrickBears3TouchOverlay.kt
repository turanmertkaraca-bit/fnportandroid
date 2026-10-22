package net.perfectdreams.butterscotch.android.frickbears3

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.PointerInputChange
import androidx.compose.ui.input.pointer.awaitFirstDown
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.sp
import kotlin.math.abs

/**
 * The FrickBears 3 touch overlay.
 *
 * FB3 is a hard, fast game: the player is flicking between cameras, slamming
 * doors and checking hallways while a power meter drains. The overlay exists to
 * put the four highest-frequency actions under the thumbs without covering the
 * game, and to let the player change camera with a swipe instead of hunting for
 * a tab inside the monitor UI.
 *
 * Design rules (see docs/controls.md for the full reasoning):
 *  - Buttons fire on press, never on release. Waiting for a release adds
 *    ~80ms of latency that is very noticeable when you are panicking.
 *  - A finger that slides off a button still triggers it. Under stress thumbs
 *    drift, and a cancel-on-slide would silently drop a door.
 *  - Doors and the monitor are latched actions in the game, so the buttons
 *    behave as toggles: one tap to engage, one tap to release.
 *  - Buttons live in the bottom band and are sized as a fraction of the
 *    viewport, so they scale from a small phone to a tablet.
 */
@Composable
fun FrickBears3TouchOverlay(
    enabled: Boolean,
    haptics: () -> Unit,
    onKeyPress: (Int) -> Unit,
    onKeyRelease: (Int) -> Unit,
    onSwipeCamera: (Int) -> Unit,
    modifier: Modifier = Modifier,
) {
    if (!enabled) return

    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        val width = maxWidth
        val height = maxHeight

        // Button size is a fraction of the shorter edge so it never gets
        // unusably small on a narrow phone nor comically large on a tablet.
        val buttonSize = minOf(width, height) * 0.17f
        val bottomInset = height * 0.06f
        val sideInset = width * 0.05f

        // Left hand: light + doors. Right hand: monitor.
        val lightButton = Fb3ButtonSpec(
            label = "LIGHT",
            subLabel = "S",
            center = Offset(sideInset + buttonSize / 2f, height - bottomInset - buttonSize / 2f),
            size = buttonSize,
            vk = Fb3Keys.VK_FLASHLIGHT,
        )
        val leftDoorButton = Fb3ButtonSpec(
            label = "L.DOOR",
            subLabel = "A",
            center = Offset(sideInset + buttonSize * 1.5f, height - bottomInset - buttonSize / 2f),
            size = buttonSize,
            vk = Fb3Keys.VK_LEFT_DOOR,
        )
        val rightDoorButton = Fb3ButtonSpec(
            label = "R.DOOR",
            subLabel = "D",
            center = Offset(sideInset + buttonSize * 2.5f, height - bottomInset - buttonSize / 2f),
            size = buttonSize,
            vk = Fb3Keys.VK_RIGHT_DOOR,
        )
        val monitorButton = Fb3ButtonSpec(
            label = "MONITOR",
            subLabel = "W",
            center = Offset(width - sideInset - buttonSize / 2f, height - bottomInset - buttonSize / 2f),
            size = buttonSize * 1.15f,
            vk = Fb3Keys.VK_MONITOR,
        )

        val buttons = listOf(lightButton, leftDoorButton, rightDoorButton, monitorButton)

        // Swipe-to-change-camera lives over the whole surface, but only
        // commits once the drag exceeds a threshold, so a stray wobble while
        // tapping the game does not switch cameras.
        var swipeAccum by remember { mutableStateOf(0f) }

        Box(
            Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    detectHorizontalDragGestures(
                        onDragStart = { swipeAccum = 0f },
                        onHorizontalDrag = { change, dragAmount ->
                            swipeAccum += dragAmount
                            change.consume()
                        },
                        onDragEnd = {
                            val threshold = size.width * 0.08f
                            if (abs(swipeAccum) >= threshold) {
                                // Dragging left moves forward through the
                                // camera list, matching the on-screen tab order.
                                onSwipeCamera(if (swipeAccum < 0f) 1 else -1)
                            }
                            swipeAccum = 0f
                        },
                        onDragCancel = { swipeAccum = 0f },
                    )
                }
        )

        buttons.forEach { spec ->
            Fb3TouchButton(
                spec = spec,
                onPressed = {
                    haptics()
                    onKeyPress(spec.vk)
                },
                onReleased = { onKeyRelease(spec.vk) },
            )
        }
    }
}

private data class Fb3ButtonSpec(
    val label: String,
    val subLabel: String,
    val center: Offset,
    val size: Dp,
    val vk: Int,
)

/**
 * One round overlay button. Press and release are reported immediately, and a
 * drag off the button does NOT cancel the press.
 */
@Composable
private fun Fb3TouchButton(
    spec: Fb3ButtonSpec,
    onPressed: () -> Unit,
    onReleased: () -> Unit,
) {
    var pressed by remember { mutableStateOf(false) }

    Box(
        Modifier
            .offset(x = spec.center.x - spec.size / 2f, y = spec.center.y - spec.size / 2f)
            .size(spec.size)
            .clip(CircleShape)
            .background(if (pressed) Color(0xFF3A4A66) else Color(0xCC1A1D24))
            .pointerInput(spec) {
                awaitEachGesture {
                    val down: PointerInputChange = awaitFirstDown(requireUnconsumed = false)
                    pressed = true
                    onPressed()
                    down.consume()

                    // Wait for the release of THIS pointer, ignoring whether it
                    // moved off the button.
                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == down.id } ?: break
                        if (!change.pressed) {
                            change.consume()
                            break
                        }
                        change.consume()
                    }

                    pressed = false
                    onReleased()
                }
            }
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = spec.label,
                color = Color.White,
                fontSize = (spec.size.value * 0.19f).sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
            )
            Text(
                text = spec.subLabel,
                color = Color(0xFF9FB4D8),
                fontSize = (spec.size.value * 0.15f).sp,
                maxLines = 1,
            )
        }
    }
}
