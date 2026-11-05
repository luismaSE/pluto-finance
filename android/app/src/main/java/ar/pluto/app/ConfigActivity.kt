package ar.pluto.app

import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.RadioGroup
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import java.util.concurrent.Executors

class ConfigActivity : AppCompatActivity() {
    private val hilo = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)   // oscuro por defecto
        super.onCreate(savedInstanceState)
        window.setFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE, android.view.WindowManager.LayoutParams.FLAG_SECURE)
        setContentView(R.layout.activity_config)
        Bordes.aplicar(this, findViewById(R.id.raiz))

        val tipo = findViewById<RadioGroup>(R.id.tipo)
        val gGithub = findViewById<View>(R.id.grupo_github)
        val gDrive = findViewById<View>(R.id.grupo_drive)
        val repo = findViewById<EditText>(R.id.gh_repo)
        val ruta = findViewById<EditText>(R.id.gh_ruta)
        val rama = findViewById<EditText>(R.id.gh_rama)
        val token = findViewById<EditText>(R.id.gh_token)
        val drive = findViewById<EditText>(R.id.drive_id)
        val resultado = findViewById<TextView>(R.id.resultado)

        val actual = Config.cargar(this)
        if (actual != null) {
            repo.setText(actual.repo); ruta.setText(actual.ruta); rama.setText(actual.rama); drive.setText(actual.driveId)
            if (actual.token.isNotBlank()) token.hint = getString(R.string.gh_token_guardado)
        }
        tipo.setOnCheckedChangeListener { _, id ->
            gGithub.visibility = if (id == R.id.tipo_github) View.VISIBLE else View.GONE
            gDrive.visibility = if (id == R.id.tipo_drive) View.VISIBLE else View.GONE
        }
        tipo.check(if (actual?.tipo == "drive") R.id.tipo_drive else R.id.tipo_github)

        fun leer() = Config(
            tipo = if (tipo.checkedRadioButtonId == R.id.tipo_drive) "drive" else "github",
            repo = repo.text.toString().trim(),
            ruta = ruta.text.toString().trim().ifBlank { "cartera.enc" },
            rama = rama.text.toString().trim().ifBlank { "main" },
            token = token.text.toString().ifBlank { actual?.token ?: "" },
            driveId = Descarga.idDrive(drive.text.toString()),
        )

        findViewById<Button>(R.id.probar).setOnClickListener {
            val c = leer()
            if (!c.completa) { resultado.text = "Completá los datos"; return@setOnClickListener }
            resultado.text = "Probando…"
            hilo.execute {
                val msg = try {
                    val b = Descarga.bajar(c)
                    "✓ Conexión correcta: archivo cifrado de ${b.size / 1024 + 1} KB"
                } catch (e: Exception) { "✗ ${e.message}" }
                runOnUiThread { resultado.text = msg }
            }
        }
        findViewById<Button>(R.id.guardar).setOnClickListener {
            val c = leer()
            if (!c.completa) { resultado.text = "Completá los datos"; return@setOnClickListener }
            Config.guardar(this, c)
            finish()
        }
        findViewById<Button>(R.id.borrar).setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("¿Borrar todo?")
                .setMessage("Se borran la configuración, el token, la huella guardada y la copia del archivo.")
                .setPositiveButton("Borrar") { _, _ -> Config.borrarTodo(this); finishAffinity() }
                .setNegativeButton("Cancelar", null)
                .show()
        }
    }
}
