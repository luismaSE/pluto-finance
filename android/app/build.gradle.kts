plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "ar.cartera.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "ar.cartera.app"
        minSdk = 26
        targetSdk = 35
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "1.0.${System.getenv("GITHUB_RUN_NUMBER") ?: "0"}"
    }

    // Firma: si existen las variables (secrets de GitHub Actions) se firma con tu clave,
    // así las actualizaciones se instalan encima sin perder la configuración.
    val ks = System.getenv("CARTERA_KEYSTORE_PATH")
    signingConfigs {
        if (ks != null && file(ks).exists()) {
            create("propia") {
                storeFile = file(ks)
                storePassword = System.getenv("CARTERA_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("CARTERA_KEY_ALIAS")
                keyPassword = System.getenv("CARTERA_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.findByName("propia") ?: signingConfigs.getByName("debug")
        }
    }

    // El dashboard es el mismo HTML que usa la PC (plantillas/dashboard.html)
    sourceSets["main"].assets.srcDirs("../../plantillas")

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.biometric:biometric:1.1.0")
    implementation("com.google.android.material:material:1.12.0")
}
