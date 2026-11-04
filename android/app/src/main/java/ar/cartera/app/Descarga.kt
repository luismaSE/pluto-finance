package ar.cartera.app

import android.content.Context
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/** Baja cartera.enc de GitHub o Drive y guarda una copia (cifrada) para usar sin conexión. */
object Descarga {
    private const val MAX_BYTES = 20 * 1024 * 1024

    private fun cache(ctx: Context) = File(ctx.filesDir, "cartera.enc")

    fun bajar(cfg: Config): ByteArray {
        val destino: Pair<URL, Map<String, String>> = when (cfg.tipo) {
            "github" -> {
                val ruta = cfg.ruta.trim('/').split("/").joinToString("/") { URLEncoder.encode(it, "UTF-8").replace("+", "%20") }
                val h = mutableMapOf(
                    "Accept" to "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version" to "2022-11-28",
                )
                if (cfg.token.isNotBlank()) h["Authorization"] = "Bearer ${cfg.token}"
                URL("https://api.github.com/repos/${cfg.repo.trim()}/contents/$ruta?ref=${URLEncoder.encode(cfg.rama, "UTF-8")}") to h
            }
            "drive" -> URL("https://drive.google.com/uc?export=download&id=${idDrive(cfg.driveId)}") to emptyMap<String, String>()
            else -> error("Origen no configurado")
        }
        val (url, headers) = destino
        val con = url.openConnection() as HttpURLConnection
        try {
            con.connectTimeout = 20_000
            con.readTimeout = 30_000
            con.instanceFollowRedirects = true
            headers.forEach { (k, v) -> con.setRequestProperty(k, v) }
            val code = con.responseCode
            if (code != 200) error(when (code) {
                401, 403 -> "Sin permiso ($code): revisá el token"
                404 -> "No encontré el archivo (404): revisá repo, ruta o link"
                else -> "El servidor respondió $code"
            })
            val bytes = con.inputStream.use { inp ->
                val out = java.io.ByteArrayOutputStream()
                val buf = ByteArray(16 * 1024)
                while (true) {
                    val n = inp.read(buf)
                    if (n < 0) break
                    out.write(buf, 0, n)
                    if (out.size() > MAX_BYTES) error("Archivo demasiado grande")
                }
                out.toByteArray()
            }
            if (!Cripto.esSobreValido(bytes)) error("El archivo descargado no es un cartera.enc válido")
            return bytes
        } finally {
            con.disconnect()
        }
    }

    /** Acepta el link completo de Drive o solo el ID. */
    fun idDrive(s: String): String {
        val t = s.trim()
        Regex("/d/([\\w-]{10,})").find(t)?.let { return it.groupValues[1] }
        Regex("[?&]id=([\\w-]{10,})").find(t)?.let { return it.groupValues[1] }
        return t
    }

    fun guardarCache(ctx: Context, b: ByteArray) {
        val tmp = File(ctx.filesDir, "cartera.enc.tmp")
        tmp.writeBytes(b)
        tmp.renameTo(cache(ctx))
    }

    fun leerCache(ctx: Context): ByteArray? = cache(ctx).takeIf { it.exists() }?.readBytes()
    fun fechaCache(ctx: Context): Long? = cache(ctx).takeIf { it.exists() }?.lastModified()
    fun borrarCache(ctx: Context) { cache(ctx).delete() }
}
