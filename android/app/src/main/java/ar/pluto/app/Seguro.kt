package ar.pluto.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyPermanentlyInvalidatedException
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Claves en el Android Keystore (hardware del teléfono, no se pueden extraer).
 * - "config": cifra el token de GitHub guardado en la app.
 * - "huella": cifra tu contraseña y SOLO se puede usar después de validar la huella.
 *   Si agregás una huella nueva al teléfono, esta clave se invalida y se vuelve a pedir la contraseña.
 */
object Seguro {
    private const val KS = "AndroidKeyStore"
    private const val CONFIG = "pluto_config"
    private const val HUELLA = "pluto_huella"
    private const val PREFS = "huella"

    private fun keystore() = KeyStore.getInstance(KS).apply { load(null) }

    private fun clave(alias: String, conHuella: Boolean): SecretKey {
        (keystore().getKey(alias, null) as? SecretKey)?.let { return it }
        val b = KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
        if (conHuella) {
            b.setUserAuthenticationRequired(true)
            b.setInvalidatedByBiometricEnrollment(true)
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                b.setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
            }
        }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, KS).apply { init(b.build()) }.generateKey()
    }

    // --- Texto de configuración ---
    fun cifrarTexto(s: String): String {
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.ENCRYPT_MODE, clave(CONFIG, false))
        return b64(c.iv) + ":" + b64(c.doFinal(s.toByteArray()))
    }

    fun descifrarTexto(s: String): String {
        val (iv, ct) = s.split(":").map { Base64.decode(it, Base64.NO_WRAP) }
        val c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.DECRYPT_MODE, clave(CONFIG, false), GCMParameterSpec(128, iv))
        return String(c.doFinal(ct))
    }

    // --- Huella ---
    fun huellaActiva(ctx: Context) = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).contains("ct")

    /** Cipher listo para cifrar la contraseña (se completa dentro del BiometricPrompt). */
    fun cipherParaGuardar(): Cipher = Cipher.getInstance("AES/GCM/NoPadding").apply {
        init(Cipher.ENCRYPT_MODE, clave(HUELLA, true))
    }

    /** Cipher listo para descifrar; null si la huella cambió y hay que volver a la contraseña. */
    fun cipherParaLeer(ctx: Context): Cipher? {
        val iv = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("iv", null) ?: return null
        return try {
            Cipher.getInstance("AES/GCM/NoPadding").apply {
                init(Cipher.DECRYPT_MODE, clave(HUELLA, true), GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
            }
        } catch (e: KeyPermanentlyInvalidatedException) {
            olvidarHuella(ctx); null
        }
    }

    fun guardarPassword(ctx: Context, cipher: Cipher, password: ByteArray) {
        val ct = cipher.doFinal(password)
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putString("iv", b64(cipher.iv)).putString("ct", b64(ct)).apply()
    }

    fun leerPassword(ctx: Context, cipher: Cipher): ByteArray {
        val ct = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("ct", null)!!
        return cipher.doFinal(Base64.decode(ct, Base64.NO_WRAP))
    }

    fun olvidarHuella(ctx: Context) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
        runCatching { keystore().deleteEntry(HUELLA) }
    }

    private fun b64(b: ByteArray) = Base64.encodeToString(b, Base64.NO_WRAP)
}
