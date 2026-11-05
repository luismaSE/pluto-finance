package ar.pluto.app

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import android.view.inputmethod.EditorInfo
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.CheckBox
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricManager.Authenticators.BIOMETRIC_STRONG
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import com.google.android.material.textfield.TextInputEditText
import java.text.DateFormat
import java.util.Date
import java.util.concurrent.Executors
import javax.crypto.Cipher

class MainActivity : AppCompatActivity() {
    private lateinit var web: WebView
    private lateinit var bloqueo: View
    private lateinit var estado: TextView
    private lateinit var password: TextInputEditText
    private lateinit var recordar: CheckBox
    private lateinit var btnDesbloquear: Button
    private lateinit var btnHuella: Button
    private lateinit var progreso: ProgressBar

    private val hilo = Executors.newSingleThreadExecutor()
    private var desbloqueado = false
    private var huellaAuto = true
    private var configPedida = false
    private val atras = object : OnBackPressedCallback(false) {
        override fun handleOnBackPressed() {
            bloquear()
            huellaAuto = false
            prepararBloqueo()
            aviso("Pluto bloqueado")
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)   // oscuro por defecto
        super.onCreate(savedInstanceState)
        // Sin capturas de pantalla y contenido oculto en "apps recientes"
        window.setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE)
        setContentView(R.layout.activity_main)
        Bordes.aplicar(this, findViewById(R.id.raiz))

        web = findViewById(R.id.web)
        bloqueo = findViewById(R.id.bloqueo)
        estado = findViewById(R.id.estado)
        password = findViewById(R.id.password)
        recordar = findViewById(R.id.recordar)
        btnDesbloquear = findViewById(R.id.desbloquear)
        btnHuella = findViewById(R.id.huella)
        progreso = findViewById(R.id.progreso)

        configurarWeb()
        btnDesbloquear.setOnClickListener { desbloquearConPassword() }
        btnHuella.setOnClickListener { desbloquearConHuella() }
        findViewById<Button>(R.id.configuracion).setOnClickListener { startActivity(Intent(this, ConfigActivity::class.java)) }
        // Sin barra superior: "atrás" bloquea el dashboard; en la pantalla de bloqueo, sale de la app
        onBackPressedDispatcher.addCallback(this, atras)
        password.setOnEditorActionListener { _, id, _ ->
            if (id == EditorInfo.IME_ACTION_DONE) { desbloquearConPassword(); true } else false
        }
    }

    private fun configurarWeb() {
        WebView.setWebContentsDebuggingEnabled(false)
        web.settings.apply {
            javaScriptEnabled = true          // el dashboard dibuja con JS
            allowFileAccess = false
            allowContentAccess = false
            blockNetworkLoads = true          // el dashboard no puede conectarse a internet
            domStorageEnabled = false
            setSupportZoom(false)
        }
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest) = true
        }
    }

    override fun onResume() {
        super.onResume()
        if (!desbloqueado) prepararBloqueo()
    }

    override fun onStop() {
        super.onStop()
        if (!isChangingConfigurations) bloquear()   // al salir de la app se bloquea sola
    }

    private fun biometriaDisponible() =
        BiometricManager.from(this).canAuthenticate(BIOMETRIC_STRONG) == BiometricManager.BIOMETRIC_SUCCESS

    private fun prepararBloqueo() {
        val cfg = Config.cargar(this)
        if (cfg == null || !cfg.completa) {
            estado.text = "Falta configurar de dónde bajar el archivo (menú → Configuración)"
            btnHuella.visibility = View.GONE
            if (!configPedida) {
                configPedida = true
                startActivity(Intent(this, ConfigActivity::class.java))
            }
            return
        }
        val origen = if (cfg.tipo == "github") "GitHub · ${cfg.repo}" else "Google Drive"
        val copia = Descarga.fechaCache(this)?.let {
            "Última copia: " + DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(it))
        } ?: "Todavía no se descargó"
        estado.text = "$origen\n$copia"
        val huella = Seguro.huellaActiva(this) && biometriaDisponible()
        btnHuella.visibility = if (huella) View.VISIBLE else View.GONE
        recordar.visibility = if (!huella && biometriaDisponible()) View.VISIBLE else View.GONE
        if (huella && huellaAuto) {
            huellaAuto = false
            desbloquearConHuella()
        }
    }

    private fun desbloquearConPassword() {
        val pw = password.text?.toString()?.toByteArray(Charsets.UTF_8) ?: return
        if (pw.isEmpty()) return
        abrir(pw, recordar.isChecked && recordar.visibility == View.VISIBLE)
    }

    private fun desbloquearConHuella() {
        val cipher = Seguro.cipherParaLeer(this)
        if (cipher == null) {
            aviso("Cambiaron las huellas del teléfono. Ingresá la contraseña.")
            prepararBloqueo()
            return
        }
        pedirHuella(cipher, "Desbloquear Pluto", { c -> abrir(Seguro.leerPassword(this, c), false) })
    }

    private fun abrir(pw: ByteArray, guardarHuella: Boolean) {
        val cfg = Config.cargar(this) ?: return
        cargando(true)
        hilo.execute {
            var avisoRed: String? = null
            val datos = try {
                Descarga.bajar(cfg).also { Descarga.guardarCache(this, it) }
            } catch (e: Exception) {
                avisoRed = "No pude actualizar (${e.message}). Muestro la última copia."
                Descarga.leerCache(this)
            }
            if (datos == null) {
                pw.fill(0)
                runOnUiThread { cargando(false); aviso(avisoRed ?: "No hay datos") }
                return@execute
            }
            try {
                val json = Cripto.descifrar(datos, pw)
                runOnUiThread {
                    mostrar(json)
                    avisoRed?.let { aviso(it) }
                    if (guardarHuella) ofrecerHuella(pw) else pw.fill(0)
                }
            } catch (e: Cripto.PasswordIncorrecta) {
                pw.fill(0)
                runOnUiThread { cargando(false); aviso("Contraseña incorrecta") }
            } catch (e: Exception) {
                pw.fill(0)
                runOnUiThread { cargando(false); aviso("No pude abrir el archivo: ${e.message}") }
            }
        }
    }

    private fun ofrecerHuella(pw: ByteArray) {
        val cipher = try { Seguro.cipherParaGuardar() } catch (e: Exception) { pw.fill(0); return }
        pedirHuella(cipher, "Confirmá tu huella para recordar la contraseña",
            ok = { c -> Seguro.guardarPassword(this, c, pw); pw.fill(0); aviso("Listo: la próxima vez entrás con la huella") },
            cancelar = { pw.fill(0) })
    }

    private fun pedirHuella(cipher: Cipher, titulo: String, ok: (Cipher) -> Unit, cancelar: () -> Unit = {}) {
        val prompt = BiometricPrompt(this, ContextCompat.getMainExecutor(this),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    result.cryptoObject?.cipher?.let(ok) ?: cancelar()
                }
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) = cancelar()
            })
        val info = BiometricPrompt.PromptInfo.Builder()
            .setTitle(titulo)
            .setNegativeButtonText("Usar contraseña")
            .setAllowedAuthenticators(BIOMETRIC_STRONG)
            .build()
        prompt.authenticate(info, BiometricPrompt.CryptoObject(cipher))
    }

    private fun mostrar(json: String) {
        val plantilla = assets.open("dashboard.html").bufferedReader().use { it.readText() }
        val fuentes = runCatching { assets.open("fuentes.css").bufferedReader().use { it.readText() } }.getOrDefault("")
        val html = plantilla.replace("/*__FUENTES__*/", fuentes).replace("/*__DATOS__*/null", json.replace("</", "<\\/"))
        web.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
        web.visibility = View.VISIBLE
        bloqueo.visibility = View.GONE
        password.setText("")
        desbloqueado = true
        atras.isEnabled = true
        cargando(false)
    }

    private fun bloquear() {
        web.loadUrl("about:blank")
        web.clearHistory()
        web.clearCache(true)
        web.visibility = View.GONE
        bloqueo.visibility = View.VISIBLE
        desbloqueado = false
        atras.isEnabled = false
        huellaAuto = true
    }

    private fun cargando(si: Boolean) {
        progreso.visibility = if (si) View.VISIBLE else View.GONE
        btnDesbloquear.isEnabled = !si
        btnHuella.isEnabled = !si
    }

    private fun aviso(s: String) = Toast.makeText(this, s, Toast.LENGTH_LONG).show()
}
