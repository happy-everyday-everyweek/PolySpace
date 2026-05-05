package com.polyspace.mobile.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.graphics.Rect
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.polyspace.mobile.accessibility.AccessibilityBridge

class PolySpaceAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        super.onServiceConnected()
        AccessibilityBridge.setService(this)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event?.let {
            AccessibilityBridge.dispatchEvent(it)
        }
    }

    override fun onInterrupt() {
        AccessibilityBridge.setService(null)
    }

    override fun onDestroy() {
        super.onDestroy()
        AccessibilityBridge.setService(null)
    }

    fun getUIHierarchy(): String {
        val rootNode = rootInActiveWindow ?: return ""
        val result = buildUIHierarchy(rootNode, 0)
        rootNode.recycle()
        return result
    }

    private fun buildUIHierarchy(node: AccessibilityNodeInfo, depth: Int): String {
        val sb = StringBuilder()
        val indent = "  ".repeat(depth)
        val bounds = Rect()
        node.getBoundsInScreen(bounds)

        sb.append("$indent<node")
        sb.append(" class=\"${node.className}\"")
        node.text?.let { sb.append(" text=\"$it\"") }
        node.contentDescription?.let { sb.append(" desc=\"$it\"") }
        node.viewIdResourceName?.let { sb.append(" id=\"$it\"") }
        sb.append(" bounds=\"${bounds.toShortString()}\"")
        sb.append(" clickable=\"${node.isClickable}\"")
        sb.append(" focusable=\"${node.isFocusable}\"")
        sb.append(" enabled=\"${node.isEnabled}\"")

        if (node.childCount == 0) {
            sb.append(" />\n")
        } else {
            sb.append(">\n")
            val childNodes = mutableListOf<AccessibilityNodeInfo>()
            for (i in 0 until node.childCount) {
                node.getChild(i)?.let { child ->
                    childNodes.add(child)
                    sb.append(buildUIHierarchy(child, depth + 1))
                }
            }
            childNodes.forEach { it.recycle() }
            sb.append("$indent</node>\n")
        }
        return sb.toString()
    }

    fun performClickAt(x: Int, y: Int): Boolean {
        val path = Path()
        path.moveTo(x.toFloat(), y.toFloat())
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 100))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    fun performLongPressAt(x: Int, y: Int): Boolean {
        val path = Path()
        path.moveTo(x.toFloat(), y.toFloat())
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, 500))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    fun performSwipe(startX: Int, startY: Int, endX: Int, endY: Int, duration: Long): Boolean {
        val path = Path()
        path.moveTo(startX.toFloat(), startY.toFloat())
        path.lineTo(endX.toFloat(), endY.toFloat())
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        return dispatchGesture(gesture, null, null)
    }

    fun performGlobalActionById(actionId: Int): Boolean {
        return performGlobalAction(actionId)
    }

    fun setTextOnNode(nodeId: String, text: String): Boolean {
        val rootNode = rootInActiveWindow ?: return false
        val node = findNodeById(rootNode, nodeId)
        val result = node?.let {
            val arguments = android.os.Bundle()
            arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
            it.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
        } ?: false
        rootNode.recycle()
        return result
    }

    private fun findNodeById(node: AccessibilityNodeInfo, nodeId: String): AccessibilityNodeInfo? {
        if (node.viewIdResourceName == nodeId) return node
        val children = mutableListOf<AccessibilityNodeInfo>()
        try {
            for (i in 0 until node.childCount) {
                node.getChild(i)?.let { child ->
                    children.add(child)
                    val found = findNodeById(child, nodeId)
                    if (found != null) return found
                }
            }
        } finally {
            children.forEach { child ->
                if (child.viewIdResourceName != nodeId) {
                    child.recycle()
                }
            }
        }
        return null
    }
}
