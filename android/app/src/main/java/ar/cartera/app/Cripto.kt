package ar.cartera.app

import android.util.Base64
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.util.zip.GZIPInputStream
import javax.crypto.Cipher
import javax.crypto.Mac
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Descifra cartera.enc. Mismo formato que cifrado.py:
 * PBKDF2-HMAC-SHA256 (contraseña en UTF-8) -> clave AES-256 -> AES-GCM -> gzip -> JSON.
 */
object Cripto {
    class PasswordIncorrecta : Exception()

    fun esSobreValido(contenido: ByteArray): Boolean = try {
        val o = JSONObject(String(contenido, Charsets.UTF_8))
        o.getInt("v") == 1 && o.has("ct") && o.has("salt") && o.has("iv")
    } catch (e: Exception) { false }

    fun descifrar(contenido: ByteArray, password: ByteArray): String {
        val env = JSONObject(String(contenido, Charsets.UTF_8))
        require(env.getInt("v") == 1 && env.getString("kdf") == "pbkdf2-sha256") { "Formato no soportado" }
        val salt = b64(env.getString("salt"))
        val iv = b64(env.getString("iv"))
        val ct = b64(env.getString("ct"))
        val clave = pbkdf2(password, salt, env.getInt("iter"))
        try {
            val c = Cipher.getInstance("AES/GCM/NoPadding")
            c.init(Cipher.DECRYPT_MODE, SecretKeySpec(clave, "AES"), GCMParameterSpec(128, iv))
            val plano = try { c.doFinal(ct) } catch (e: javax.crypto.AEADBadTagException) { throw PasswordIncorrecta() }
            return GZIPInputStream(ByteArrayInputStream(plano)).use { it.readBytes() }.toString(Charsets.UTF_8)
        } finally {
            clave.fill(0)
        }
    }

    /** PBKDF2 con un único bloque (32 bytes = largo de SHA-256). */
    private fun pbkdf2(password: ByteArray, salt: ByteArray, iteraciones: Int): ByteArray {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(password, "HmacSHA256"))
        mac.update(salt)
        mac.update(byteArrayOf(0, 0, 0, 1))
        var u = mac.doFinal()
        val t = u.copyOf()
        for (i in 1 until iteraciones) {
            u = mac.doFinal(u)
            for (j in t.indices) t[j] = (t[j].toInt() xor u[j].toInt()).toByte()
        }
        return t
    }

    private fun b64(s: String) = Base64.decode(s, Base64.DEFAULT)
}
