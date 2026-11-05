package ar.pluto.app

import android.content.Context

/** Configuración del origen del archivo. El token se guarda cifrado con una clave del Keystore. */
data class Config(
    val tipo: String,          // "github" | "drive"
    val repo: String = "",
    val ruta: String = "cartera.enc",
    val rama: String = "main",
    val token: String = "",
    val driveId: String = "",
) {
    val completa get() = when (tipo) {
        "github" -> repo.contains("/") && ruta.isNotBlank()
        "drive" -> driveId.isNotBlank()
        else -> false
    }

    companion object {
        private const val PREFS = "config"

        fun cargar(ctx: Context): Config? {
            val p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            val tipo = p.getString("tipo", null) ?: return null
            val token = p.getString("token", null)?.let { runCatching { Seguro.descifrarTexto(it) }.getOrNull() } ?: ""
            return Config(tipo, p.getString("repo", "")!!, p.getString("ruta", "cartera.enc")!!,
                p.getString("rama", "main")!!, token, p.getString("driveId", "")!!)
        }

        fun guardar(ctx: Context, c: Config) {
            ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putString("tipo", c.tipo).putString("repo", c.repo.trim()).putString("ruta", c.ruta.trim())
                .putString("rama", c.rama.trim()).putString("driveId", c.driveId.trim())
                .putString("token", if (c.token.isBlank()) null else Seguro.cifrarTexto(c.token.trim()))
                .apply()
        }

        fun borrarTodo(ctx: Context) {
            ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply()
            Seguro.olvidarHuella(ctx)
            Descarga.borrarCache(ctx)
        }
    }
}
