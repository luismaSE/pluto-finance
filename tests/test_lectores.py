"""Lectores de PDF probados con textos INVENTADOS que imitan el formato de cada resumen."""
from conectores.pdf import galicia_caja, galicia_fci, mercadopago

CAJA = """                                 Resumen de Caja de Ahorro en Pesos
      JUAN PEREZ                        CUIL del Responsable Impositivo : 20-00000000-0
Datos de la cuenta                            Período de movimientos                      Saldos
      Caja de Ahorro en Pesos                                                                $10.000,00
      CBU                                         01/10/2026                 31/10/2026      $13.400,00
Movimientos
Fecha       Descripción                        Origen               Crédito                 Débito                Saldo
02/10/26    TRANSFERENCIA A TERCEROS                                                       -1.500,00         8.500,00
            COMERCIO DE PRUEBA SA
            30000000000
05/10/26    ACREDITAMIENTO DE HABERES          00D5                 6.000,00                                14.500,00
            EMPRESA FICTICIA SA
10/10/26    PAGO TARJETA VISA                                                              -1.100,00        13.400,00
            OPERACION 1234567890
     Total                                                           $ 6.000,00                 -$ 2.600,00                    $ 13.400,00
Banco de Galicia y Buenos Aires S.A.U.
"""

FCI = """Posicion al 30/09/2026
FIMA-FONDOS COMUNES DE INVERSION
Fondo                                                     Tenencias en Cuotas           Valor Cuota(*)        Saldo Valorizado
FONDO PRUEBA CLASE A                                                 1.000,00           $ 100,000000          $ 100.000,00
FONDO DOLARES CLASE A                                                  500,00USD 1,000000USD 500,00
"""

MP = """RESUMEN DE CUENTA EN PESOS
Juan Perez
CVU: 0000000000000000000000   CUIT/ CUIL: 20000000000
Periodo: Del 1 al 31 de octubre de 2026
Saldo inicial: $ 1.000,00   Entradas: $ 5.000,00   Saldo final: $ 4.500,00
DETALLE DE MOVIMIENTOS
Fecha   Descripción   ID de la   Valor   Saldo
02-10-2026   Rendimientos   111111111111   $ 10,00   $ 1.010,00
03-10-2026   Transferencia enviada Comercio   222222222222   $ -510,00   $ 500,00
   De Prueba
   Transferencia recibida JUAN
05-10-2026   PEREZ   333333333333   $ 4.990,00   $ 5.490,00
06-10-2026   Pago con QR Kiosco Uno   444444444444   $ -990,00   $ 4.500,00
www.mercadopago.com.ar
"""


def test_galicia_caja():
    assert galicia_caja.detectar(CAJA)
    r = galicia_caja.parsear(CAJA)
    assert r.titular == "JUAN PEREZ"
    assert r.cuentas[0].saldo == 13400.0 and r.cuentas[0].moneda == "ARS" and r.cuentas[0].al == "2026-10-31"
    assert [m.monto for m in r.movimientos] == [-1500.0, 6000.0, -1100.0]
    assert r.movimientos[0].descripcion == "TRANSFERENCIA A TERCEROS · COMERCIO DE PRUEBA SA"
    assert r.movimientos[2].descripcion == "PAGO TARJETA VISA"          # el número de operación no ensucia
    assert r.cobertura == {"entidad": "Galicia", "cuenta": "Caja de ahorro en pesos", "desde": "2026-10-01", "hasta": "2026-10-31"}
    assert r.advertencias == []                                           # los saldos cierran


def test_galicia_caja_detecta_saldos_que_no_cierran():
    roto = CAJA.replace("13.400,00\n            OPERACION", "13.000,00\n            OPERACION")
    assert galicia_caja.parsear(roto).advertencias


def test_galicia_fci():
    assert galicia_fci.detectar(FCI)
    r = galicia_fci.parsear(FCI)
    assert [(i.valuacion, i.moneda, i.tipo) for i in r.inversiones] == [(100000.0, "ARS", "FCI"), (500.0, "USD", "FCI")]
    assert r.inversiones[0].al == "2026-09-30"


def test_mercadopago():
    assert mercadopago.detectar(MP)
    r = mercadopago.parsear(MP)
    assert r.titular == "Juan Perez"
    assert r.cuentas[0].saldo == 4500.0
    descs = [m.descripcion for m in r.movimientos]
    assert descs[1] == "Transferencia enviada Comercio De Prueba"        # descripción partida en dos líneas
    assert descs[2] == "Transferencia recibida JUAN PEREZ"               # prefijo antes de la fecha
    assert (r.cobertura["desde"], r.cobertura["hasta"]) == ("2026-10-01", "2026-10-31")
    assert r.advertencias == []


def test_formatos_no_se_confunden():
    assert not mercadopago.detectar(CAJA) and not galicia_fci.detectar(CAJA)
    assert not galicia_caja.detectar(MP)
