package com.polyspace.mobile.accessibility

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.view.accessibility.AccessibilityEvent
import com.polyspace.mobile.service.PolySpaceAccessibilityService
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

data class LightweightAccessibilityEvent(
    val eventType: Int,
    val packageName: String?,
    val className: String?,
    val text: String?,
    val contentDescription: String?,
    val sourceViewId: String?,
    val timestamp: Long
)

object AccessibilityBridge {

    private var service: PolySpaceAccessibilityService? = null
    private val _events = MutableSharedFlow<LightweightAccessibilityEvent>(extraBufferCapacity = 16)
    val events: SharedFlow<LightweightAccessibilityEvent> = _events

    internal lateinit var appContext: Context

    fun init(context: Context) {
        appContext = context.applicationContext
    }

    fun setService(service: PolySpaceAccessibilityService?) {
        this.service = service
    }

    fun isServiceRunning(): Boolean = service != null

    fun dispatchEvent(event: AccessibilityEvent) {
        val lightweight = LightweightAccessibilityEvent(
            eventType = event.eventType,
            packageName = event.packageName?.toString(),
            className = event.className?.toString(),
            text = event.text?.firstOrNull()?.toString(),
            contentDescription = event.contentDescription?.toString(),
            sourceViewId = event.source?.viewIdResourceName,
            timestamp = event.eventTime
        )
        _events.tryEmit(lightweight)
    }

    fun getUIHierarchy(): String? {
        return service?.getUIHierarchy()
    }

    fun performClick(x: Int, y: Int): Boolean {
        return service?.performClickAt(x, y) ?: false
    }

    fun performLongPress(x: Int, y: Int): Boolean {
        return service?.performLongPressAt(x, y) ?: false
    }

    fun performSwipe(startX: Int, startY: Int, endX: Int, endY: Int, duration: Long): Boolean {
        return service?.performSwipe(startX, startY, endX, endY, duration) ?: false
    }

    fun performGlobalAction(actionId: Int): Boolean {
        return service?.performGlobalActionById(actionId) ?: false
    }

    fun setTextOnNode(nodeId: String, text: String): Boolean {
        return service?.setTextOnNode(nodeId, text) ?: false
    }

    fun takeScreenshot(path: String, format: String): Boolean {
        return try {
            val svc = service ?: return false
            val latch = CountDownLatch(1)
            val resultHolder = booleanArrayOf(false)
            svc.takeScreenshot(
                android.view.Display.DEFAULT_DISPLAY,
                { runnable -> runnable.run() },
                object : AccessibilityService.TakeScreenshotCallback {
                    override fun onSuccess(screenshot: AccessibilityService.ScreenshotResult) {
                        try {
                            val bitmap = android.graphics.Bitmap.wrapHardwareBuffer(
                                screenshot.hardwareBuffer,
                                screenshot.colorSpace
                            ) ?: run { latch.countDown(); return }
                            val softwareBitmap = bitmap.copy(
                                android.graphics.Bitmap.Config.ARGB_8888,
                                false
                            )
                            if (softwareBitmap != null) {
                                val file = java.io.File(path)
                                java.io.FileOutputStream(file).use { fos ->
                                    val compressFormat = when (format.lowercase()) {
                                        "jpg", "jpeg" -> android.graphics.Bitmap.CompressFormat.JPEG
                                        else -> android.graphics.Bitmap.CompressFormat.PNG
                                    }
                                    softwareBitmap.compress(compressFormat, 90, fos)
                                }
                                resultHolder[0] = true
                                softwareBitmap.recycle()
                            }
                        } finally {
                            screenshot.hardwareBuffer.close()
                            latch.countDown()
                        }
                    }

                    override fun onFailure(errorCode: Int) {
                        resultHolder[0] = false
                        latch.countDown()
                    }
                }
            )
            latch.await(3, TimeUnit.SECONDS)
            resultHolder[0]
        } catch (e: Exception) {
            false
        }
    }

    fun getCurrentActivityName(): String? {
        val svc = service ?: return null
        val rootNode = svc.rootInActiveWindow ?: return null
        val name = rootNode.packageName?.toString()
        rootNode.recycle()
        return name
    }
}
