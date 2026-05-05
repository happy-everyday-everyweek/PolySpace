package com.polyspace.mobile.linux

import android.content.Context
import android.os.Build
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.util.zip.GZIPInputStream
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream

object LinuxManager {

    private const val TAG = "LinuxManager"
    private const val LINUX_DIR = "linux"
    private const val ROOTFS_DIR = "rootfs"
    private const val PROOT_DIR = "proot"

    private var linuxProcess: Process? = null

    interface ExtractionProgressCallback {
        fun onProgress(phase: String, progress: Float)
    }

    private var progressCallback: ExtractionProgressCallback? = null

    fun setProgressCallback(callback: ExtractionProgressCallback?) {
        progressCallback = callback
    }

    fun isLinuxAvailable(context: Context): Boolean {
        val rootfs = getRootfsDir(context)
        return rootfs.exists() && File(rootfs, "home/polyspace/start.sh").exists()
    }

    fun isBackendReady(context: Context): Boolean {
        val rootfs = getRootfsDir(context)
        return rootfs.exists() && File(rootfs, "home/polyspace/start.sh").exists()
    }

    fun extractLinuxDist(context: Context): Boolean {
        return try {
            val linuxDir = getLinuxDir(context)
            val rootfsDir = File(linuxDir, ROOTFS_DIR)
            val prootDir = File(linuxDir, PROOT_DIR)

            if (rootfsDir.exists() && File(rootfsDir, "home/polyspace/start.sh").exists()) {
                Log.i(TAG, "Linux dist already extracted")
                extractProotBinary(context, prootDir, getAbiDir())
                return true
            }

            if (rootfsDir.exists() && !File(rootfsDir, "home/polyspace/start.sh").exists()) {
                Log.w(TAG, "Rootfs dir exists but incomplete, removing for re-extraction")
                rootfsDir.deleteRecursively()
            }

            val abiDir = getAbiDir()
            Log.i(TAG, "Device ABI: ${Build.SUPPORTED_ABIS[0]}, using: $abiDir")

            progressCallback?.onProgress("extracting_proot", 0.02f)
            extractProotBinary(context, prootDir, abiDir)

            progressCallback?.onProgress("extracting_rootfs", 0.05f)
            val result = extractRootfsJava(context, rootfsDir, abiDir)
            if (!result) {
                Log.e(TAG, "Rootfs extraction failed")
                return false
            }

            val startSh = File(rootfsDir, "home/polyspace/start.sh")
            if (!startSh.exists()) {
                Log.e(TAG, "Extraction completed but start.sh not found at ${startSh.absolutePath}")
                val files = rootfsDir.listFiles()?.map { it.name }?.take(20) ?: emptyList()
                Log.e(TAG, "Rootfs top-level contents: $files")
                return false
            }

            progressCallback?.onProgress("extraction_complete", 1.0f)
            Log.i(TAG, "Linux dist extraction complete")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract Linux dist", e)
            false
        }
    }

    private fun getAbiDir(): String {
        val abi = Build.SUPPORTED_ABIS[0]
        return when (abi) {
            "arm64-v8a" -> "arm64-v8a"
            "x86_64" -> "x86_64"
            "x86" -> "x86"
            else -> "arm64-v8a"
        }
    }

    private fun extractProotBinary(context: Context, targetDir: File, abiDir: String): Boolean {
        val prootFile = File(targetDir, "proot")
        if (prootFile.exists() && prootFile.canExecute()) {
            Log.i(TAG, "proot binary already exists")
            return true
        }

        targetDir.mkdirs()

        val assetAbi = when (abiDir) {
            "arm64-v8a" -> "arm64-v8a"
            "x86_64" -> "x86_64"
            "x86" -> "x86"
            else -> "arm64-v8a"
        }
        val assetPath = "proot/$assetAbi/proot"
        return try {
            context.assets.open(assetPath).use { input ->
                FileOutputStream(prootFile).use { output ->
                    input.copyTo(output, 65536)
                }
            }
            prootFile.setExecutable(true, false)
            prootFile.setReadable(true, false)
            Log.i(TAG, "Extracted proot from assets/$assetPath (${prootFile.length()} bytes)")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract proot from assets/$assetPath", e)
            false
        }
    }

    private fun getRootfsArchiveName(abiDir: String): String {
        return when (abiDir) {
            "x86_64" -> "alpine-rootfs-x86_64.tar.gz"
            else -> "alpine-rootfs-aarch64.tar.gz"
        }
    }

    private fun extractRootfsJava(context: Context, targetDir: File, abiDir: String): Boolean {
        val rootfsArchive = getRootfsArchiveName(abiDir)
        Log.i(TAG, "Extracting rootfs from assets/$rootfsArchive using Java...")
        val startTime = System.currentTimeMillis()

        return try {
            targetDir.mkdirs()

            val assetFd = context.assets.openFd(rootfsArchive)
            val totalSize = assetFd.length
            assetFd.close()

            var entryCount = 0
            var lastProgressLog = 0L
            var bytesExtracted = 0L
            context.assets.open(rootfsArchive).use { input ->
                val gzipStream = GZIPInputStream(input, 65536)
                val tarReader = TarArchiveInputStream(gzipStream)

                var entry = tarReader.nextTarEntry
                while (entry != null) {
                    val entryName = entry.name
                    if (entryName.contains("..")) {
                        entry = tarReader.nextTarEntry
                        continue
                    }
                    val outputFile = File(targetDir, entryName)
                    if (entry.isDirectory) {
                        outputFile.mkdirs()
                    } else {
                        outputFile.parentFile?.mkdirs()
                        FileOutputStream(outputFile).use { output ->
                            val buf = ByteArray(65536)
                            var len: Int
                            while (tarReader.read(buf).also { len = it } != -1) {
                                output.write(buf, 0, len)
                                bytesExtracted += len
                            }
                        }
                        if (entry.mode and 0x100 != 0) {
                            outputFile.setExecutable(true, false)
                        }
                        outputFile.setReadable(true, false)
                    }
                    entryCount++
                    val now = System.currentTimeMillis()
                    if (totalSize > 0 && now - lastProgressLog > 200) {
                        val progress = 0.05f + 0.90f * (bytesExtracted.toFloat() / totalSize.toFloat()).coerceAtMost(1f)
                        progressCallback?.onProgress("extracting_rootfs", progress)
                        lastProgressLog = now
                    }
                    if (now - lastProgressLog > 3000) {
                        Log.i(TAG, "Extraction progress: $entryCount entries, ${bytesExtracted / 1024}KB extracted")
                        lastProgressLog = now
                    }
                    entry = tarReader.nextTarEntry
                }
            }

            val elapsed = System.currentTimeMillis() - startTime
            Log.i(TAG, "Rootfs extraction completed in ${elapsed}ms ($entryCount entries)")

            val startSh = File(targetDir, "home/polyspace/start.sh")
            if (startSh.exists()) {
                startSh.setExecutable(true, false)
            }
            true
        } catch (e: Exception) {
            Log.e(TAG, "Rootfs extraction failed", e)
            if (targetDir.exists()) {
                Log.w(TAG, "Cleaning up incomplete extraction")
                targetDir.deleteRecursively()
            }
            false
        }
    }

    fun startLinuxBackend(
        context: Context,
        port: Int = 8000,
        onOutput: (String) -> Unit = {},
        onError: (String) -> Unit = {}
    ): Boolean {
        if (linuxProcess != null && linuxProcess!!.isAlive) {
            Log.i(TAG, "Linux backend already running")
            return true
        }

        val linuxDir = getLinuxDir(context)
        val proot = File(linuxDir, "$PROOT_DIR/proot")
        val rootfs = File(linuxDir, ROOTFS_DIR)

        if (!proot.exists()) {
            onError("proot binary not found. Please extract Linux distribution first.")
            return false
        }
        if (!rootfs.exists()) {
            onError("RootFS not found. Please extract Linux distribution first.")
            return false
        }

        return try {
            val dataDir = File(context.filesDir, "polyspace_data")
            dataDir.mkdirs()

            val cmd = mutableListOf(
                proot.absolutePath,
                "-0",
                "-r", rootfs.absolutePath,
                "-b", "/dev",
                "-b", "/proc",
                "-b", "/sys",
                "-b", "${dataDir.absolutePath}:/home/polyspace/data",
                "-b", "${rootfs.absolutePath}/home/polyspace/backend:/home/polyspace/backend",
                "/home/polyspace/start.sh"
            )

            val processBuilder = ProcessBuilder()
            processBuilder.command(cmd)
            processBuilder.environment()["POLYSPACE_PORT"] = port.toString()
            processBuilder.environment()["POLYSPACE_DATA_DIR"] = "/home/polyspace/data"
            processBuilder.redirectErrorStream(true)

            Log.i(TAG, "Starting Linux backend on port $port...")
            linuxProcess = processBuilder.start()

            Thread {
                try {
                    linuxProcess?.inputStream?.bufferedReader()?.use { reader ->
                        var line: String?
                        while (reader.readLine().also { line = it } != null) {
                            line?.let {
                                Log.d(TAG, it)
                                onOutput(it)
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Process read error", e)
                    onError(e.message ?: "Process read error")
                }
            }.start()

            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start Linux backend", e)
            onError(e.message ?: "Failed to start Linux backend")
            false
        }
    }

    fun stopLinuxBackend() {
        linuxProcess?.destroy()
        linuxProcess = null
        Log.i(TAG, "Linux backend stopped")
    }

    fun isRunning(): Boolean = linuxProcess?.isAlive == true

    private fun getLinuxDir(context: Context) = File(context.filesDir, LINUX_DIR)
    private fun getRootfsDir(context: Context) = File(getLinuxDir(context), ROOTFS_DIR)

    fun getRootfsSize(context: Context): Long {
        val rootfs = getRootfsDir(context)
        return if (rootfs.exists()) calculateDirectorySize(rootfs) else 0L
    }

    private fun calculateDirectorySize(dir: File): Long {
        var size = 0L
        if (dir.exists()) {
            dir.walkTopDown().forEach { file ->
                if (file.isFile) size += file.length()
            }
        }
        return size
    }
}
