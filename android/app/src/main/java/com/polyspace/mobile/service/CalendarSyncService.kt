package com.polyspace.mobile.service

import android.Manifest
import android.content.ContentResolver
import android.content.ContentValues
import android.content.Context
import android.content.pm.PackageManager
import android.provider.CalendarContract
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.ListenableWorker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

object CalendarSyncService {

    private const val TAG = "CalendarSync"

    enum class SyncDirection {
        TO_SYSTEM,
        FROM_SYSTEM,
        BOTH
    }

    enum class ConflictResolution {
        LAST_WRITE_WINS,
        KEEP_BOTH,
        SKIP
    }

    data class SyncResult(
        val synced: Int,
        val conflicts: Int,
        val skipped: Int,
        val errors: Int
    )

    fun hasCalendarPermission(context: Context): Boolean {
        val read = ContextCompat.checkSelfPermission(
            context, Manifest.permission.READ_CALENDAR
        ) == PackageManager.PERMISSION_GRANTED
        val write = ContextCompat.checkSelfPermission(
            context, Manifest.permission.WRITE_CALENDAR
        ) == PackageManager.PERMISSION_GRANTED
        return read && write
    }

    suspend fun syncToSystemCalendar(
        context: Context,
        host: String,
        port: Int,
        resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS
    ): Result<SyncResult> = withContext(Dispatchers.IO) {
        try {
            val events = fetchPolySpaceEvents(host, port)
            if (events.isEmpty()) {
                return@withContext Result.success(SyncResult(0, 0, 0, 0))
            }

            val resolver = context.contentResolver
            val polySpaceCalendarId = getOrCreatePolySpaceCalendar(resolver)
            var synced = 0
            var conflicts = 0
            var skipped = 0
            var errors = 0

            for (event in events) {
                val polyspaceId = event.optString("id", "")
                val polyspaceUpdatedAt = event.optLong("updated_at", 0L)
                val existingId = findExistingEvent(resolver, polySpaceCalendarId, polyspaceId)

                if (existingId != null) {
                    val systemUpdatedAt = getEventLastUpdated(resolver, existingId)
                    if (systemUpdatedAt > 0 && polyspaceUpdatedAt > 0 && systemUpdatedAt > polyspaceUpdatedAt) {
                        when (resolution) {
                            ConflictResolution.LAST_WRITE_WINS -> {
                                val values = eventToContentValues(event, polySpaceCalendarId)
                                resolver.update(
                                    CalendarContract.Events.CONTENT_URI.buildUpon()
                                        .appendPath(existingId).build(),
                                    values, null, null
                                )
                                conflicts++
                            }
                            ConflictResolution.KEEP_BOTH -> {
                                val values = eventToContentValues(event, polySpaceCalendarId)
                                values.put(CalendarContract.Events.TITLE,
                                    event.optString("title", "") + " (PolySpace)")
                                resolver.insert(CalendarContract.Events.CONTENT_URI, values)
                                conflicts++
                            }
                            ConflictResolution.SKIP -> {
                                skipped++
                                continue
                            }
                        }
                    } else {
                        val values = eventToContentValues(event, polySpaceCalendarId)
                        resolver.update(
                            CalendarContract.Events.CONTENT_URI.buildUpon()
                                .appendPath(existingId).build(),
                            values, null, null
                        )
                    }
                    synced++
                } else {
                    val values = eventToContentValues(event, polySpaceCalendarId)
                    resolver.insert(CalendarContract.Events.CONTENT_URI, values)
                    synced++
                }
            }

            Log.i(TAG, "Synced $synced events to system calendar ($conflicts conflicts, $skipped skipped)")
            Result.success(SyncResult(synced, conflicts, skipped, errors))
        } catch (e: Exception) {
            Log.e(TAG, "Failed to sync to system calendar", e)
            Result.failure(e)
        }
    }

    suspend fun syncFromSystemCalendar(
        context: Context,
        host: String,
        port: Int
    ): Result<SyncResult> = withContext(Dispatchers.IO) {
        try {
            val resolver = context.contentResolver
            val systemEvents = readSystemCalendarEvents(resolver)
            if (systemEvents.isEmpty()) {
                return@withContext Result.success(SyncResult(0, 0, 0, 0))
            }

            var synced = 0
            var errors = 0
            for (event in systemEvents) {
                val success = pushEventToPolySpace(host, port, event)
                if (success) synced++ else errors++
            }

            Log.i(TAG, "Synced $synced events from system calendar")
            Result.success(SyncResult(synced, 0, 0, errors))
        } catch (e: Exception) {
            Log.e(TAG, "Failed to sync from system calendar", e)
            Result.failure(e)
        }
    }

    suspend fun syncBoth(
        context: Context,
        host: String,
        port: Int,
        resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS
    ): Result<Pair<SyncResult, SyncResult>> = withContext(Dispatchers.IO) {
        val toResult = syncToSystemCalendar(context, host, port, resolution)
        val fromResult = syncFromSystemCalendar(context, host, port)

        if (toResult.isFailure) return@withContext Result.failure(toResult.exceptionOrNull()!!)
        if (fromResult.isFailure) return@withContext Result.failure(fromResult.exceptionOrNull()!!)

        Result.success(Pair(toResult.getOrDefault(SyncResult(0,0,0,0)), fromResult.getOrDefault(SyncResult(0,0,0,0))))
    }

    private fun getEventLastUpdated(resolver: ContentResolver, eventId: String): Long {
        val projection = arrayOf(CalendarContract.Events.LAST_DATE)
        resolver.query(
            CalendarContract.Events.CONTENT_URI.buildUpon().appendPath(eventId).build(),
            projection, null, null, null
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getLong(0)
            }
        }
        return 0L
    }

    private fun fetchPolySpaceEvents(host: String, port: Int): List<JSONObject> {
        var conn: HttpURLConnection? = null
        return try {
            val url = URL("http://$host:$port/api/v1/ai/coordination/calendar/events")
            conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 10000
            conn.readTimeout = 10000

            if (conn.responseCode != 200) {
                return emptyList()
            }

            val response = conn.inputStream.bufferedReader().readText()

            val json = JSONObject(response)
            val eventsArray = json.optJSONArray("events") ?: return emptyList()

            (0 until eventsArray.length()).map { eventsArray.getJSONObject(it) }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch PolySpace events", e)
            emptyList()
        } finally {
            conn?.disconnect()
        }
    }

    private fun getOrCreatePolySpaceCalendar(resolver: ContentResolver): Long {
        val projection = arrayOf(
            CalendarContract.Calendars._ID,
            CalendarContract.Calendars.ACCOUNT_NAME
        )
        val selection = "${CalendarContract.Calendars.ACCOUNT_NAME} = ?"
        val selectionArgs = arrayOf("polyspace@local")

        resolver.query(
            CalendarContract.Calendars.CONTENT_URI,
            projection, selection, selectionArgs, null
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getLong(0)
            }
        }

        val values = ContentValues().apply {
            put(CalendarContract.Calendars.ACCOUNT_NAME, "polyspace@local")
            put(CalendarContract.Calendars.ACCOUNT_TYPE, "LOCAL")
            put(CalendarContract.Calendars.NAME, "聚境日历")
            put(CalendarContract.Calendars.CALENDAR_DISPLAY_NAME, "聚境日历")
            put(CalendarContract.Calendars.CALENDAR_COLOR, 0xFF555555.toInt())
            put(CalendarContract.Calendars.CALENDAR_ACCESS_LEVEL, CalendarContract.Calendars.CAL_ACCESS_OWNER)
            put(CalendarContract.Calendars.OWNER_ACCOUNT, "polyspace@local")
            put(CalendarContract.Calendars.VISIBLE, 1)
            put(CalendarContract.Calendars.SYNC_EVENTS, 1)
        }

        val uri = resolver.insert(
            CalendarContract.Calendars.CONTENT_URI.buildUpon()
                .appendQueryParameter(CalendarContract.CALLER_IS_SYNCADAPTER, "true")
                .appendQueryParameter(CalendarContract.Calendars.ACCOUNT_NAME, "polyspace@local")
                .appendQueryParameter(CalendarContract.Calendars.ACCOUNT_TYPE, "LOCAL")
                .build(),
            values
        )

        return uri?.lastPathSegment?.toLongOrNull() ?: 1L
    }

    private fun findExistingEvent(
        resolver: ContentResolver,
        calendarId: Long,
        polyspaceId: String
    ): String? {
        val selection = "${CalendarContract.Events.CALENDAR_ID} = ? AND ${CalendarContract.Events.DESCRIPTION} LIKE ?"
        val selectionArgs = arrayOf(calendarId.toString(), "%polyspace_id:$polyspaceId%")

        resolver.query(
            CalendarContract.Events.CONTENT_URI,
            arrayOf(CalendarContract.Events._ID),
            selection, selectionArgs, null
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                return cursor.getString(0)
            }
        }
        return null
    }

    private fun eventToContentValues(event: JSONObject, calendarId: Long): ContentValues {
        val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        sdf.timeZone = TimeZone.getTimeZone("UTC")

        val startTime = event.optString("start_time", "")
        val endTime = event.optString("end_time", "")
        val startMillis = if (startTime.isNotEmpty()) {
            sdf.parse(startTime)?.time ?: System.currentTimeMillis()
        } else System.currentTimeMillis()
        val endMillis = if (endTime.isNotEmpty()) {
            sdf.parse(endTime)?.time ?: startMillis + 3600000
        } else startMillis + 3600000

        return ContentValues().apply {
            put(CalendarContract.Events.CALENDAR_ID, calendarId)
            put(CalendarContract.Events.TITLE, event.optString("title", ""))
            put(CalendarContract.Events.DESCRIPTION,
                event.optString("description", "") + "\n[polyspace_id:${event.optString("id", "")}]")
            put(CalendarContract.Events.EVENT_LOCATION, event.optString("location", ""))
            put(CalendarContract.Events.DTSTART, startMillis)
            put(CalendarContract.Events.DTEND, endMillis)
            put(CalendarContract.Events.EVENT_TIMEZONE, TimeZone.getDefault().id)
        }
    }

    private fun readSystemCalendarEvents(resolver: ContentResolver): List<JSONObject> {
        val now = System.currentTimeMillis()
        val threeMonths = 90L * 24 * 60 * 60 * 1000

        val projection = arrayOf(
            CalendarContract.Events._ID,
            CalendarContract.Events.TITLE,
            CalendarContract.Events.DESCRIPTION,
            CalendarContract.Events.EVENT_LOCATION,
            CalendarContract.Events.DTSTART,
            CalendarContract.Events.DTEND,
            CalendarContract.Events.EVENT_TIMEZONE
        )

        val selection = "${CalendarContract.Events.DTSTART} >= ? AND ${CalendarContract.Events.DTSTART} <= ?"
        val selectionArgs = arrayOf(now.toString(), (now + threeMonths).toString())

        val events = mutableListOf<JSONObject>()

        resolver.query(
            CalendarContract.Events.CONTENT_URI,
            projection, selection, selectionArgs,
            "${CalendarContract.Events.DTSTART} ASC"
        )?.use { cursor ->
            val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
            while (cursor.moveToNext()) {
                val event = JSONObject().apply {
                    put("system_event_id", cursor.getString(0))
                    put("title", cursor.getString(1) ?: "")
                    put("description", cursor.getString(2) ?: "")
                    put("location", cursor.getString(3) ?: "")
                    val dtStart = cursor.getLong(4)
                    val dtEnd = cursor.getLong(5)
                    put("start_time", sdf.format(dtStart))
                    put("end_time", if (dtEnd > 0) sdf.format(dtEnd) else sdf.format(dtStart + 3600000))
                    put("timezone", cursor.getString(6) ?: TimeZone.getDefault().id)
                    put("source", "system_calendar")
                }
                events.add(event)
            }
        }

        return events
    }

    private fun pushEventToPolySpace(host: String, port: Int, event: JSONObject): Boolean {
        val url = URL("http://$host:$port/api/v1/ai/coordination/calendar/events")
        val conn = url.openConnection() as HttpURLConnection
        conn.requestMethod = "POST"
        conn.doOutput = true
        conn.setRequestProperty("Content-Type", "application/json")
        conn.connectTimeout = 10000
        conn.readTimeout = 10000

        conn.outputStream.use { os ->
            os.write(event.toString().toByteArray())
        }

        val success = conn.responseCode in 200..299
        conn.disconnect()
        return success
    }
}

class CalendarSyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    override suspend fun doWork(): ListenableWorker.Result {
        val host = inputData.getString("host") ?: "localhost"
        val port = inputData.getInt("port", 8000)

        val result = CalendarSyncService.syncBoth(applicationContext, host, port)
        return if (result.isSuccess) ListenableWorker.Result.success() else ListenableWorker.Result.retry()
    }
}
