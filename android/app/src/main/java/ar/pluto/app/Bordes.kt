package ar.pluto.app

import android.app.Activity
import android.view.View
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat

/**
 * Android 15 dibuja las apps de borde a borde. Sin esto, la barra de estado queda
 * encima del contenido y se ve lo que hay detrás. Se deja un margen exacto para las
 * barras del sistema y el recorte de la cámara, pintado con el color de fondo.
 */
object Bordes {
    fun aplicar(actividad: Activity, raiz: View) {
        WindowCompat.setDecorFitsSystemWindows(actividad.window, false)
        WindowCompat.getInsetsController(actividad.window, raiz).apply {
            isAppearanceLightStatusBars = false        // la app es oscura: íconos claros
            isAppearanceLightNavigationBars = false
        }
        ViewCompat.setOnApplyWindowInsetsListener(raiz) { v, insets ->
            val b = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout() or WindowInsetsCompat.Type.ime()
            )
            v.setPadding(b.left, b.top, b.right, b.bottom)
            WindowInsetsCompat.CONSUMED
        }
    }
}
