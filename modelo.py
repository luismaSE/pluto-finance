"""Formato común para los datos de todas las entidades."""
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Cuenta:
    entidad: str
    tipo: str          # "Caja de ahorro", "Dinero disponible", ...
    moneda: str        # "ARS" | "USD"
    saldo: float
    al: str | None = None   # fecha del saldo (ISO)


@dataclass
class Movimiento:
    fecha: str         # ISO "YYYY-MM-DD"
    entidad: str
    descripcion: str
    monto: float       # negativo = gasto / egreso
    moneda: str
    categoria: str = ""


@dataclass
class Inversion:
    entidad: str
    activo: str        # ticker o nombre del fondo
    descripcion: str
    tipo: str          # "ACCIONES", "CEDEARS", "FCI", "PLAZO FIJO", ...
    cantidad: float
    valuacion: float
    moneda: str
    variacion_dia_pct: float | None = None
    ganancia_pct: float | None = None
    ganancia: float | None = None
    al: str | None = None


@dataclass
class Snapshot:
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="minutes"))
    cuentas: list[Cuenta] = field(default_factory=list)
    movimientos: list[Movimiento] = field(default_factory=list)
    inversiones: list[Inversion] = field(default_factory=list)
    cotizaciones: dict = field(default_factory=dict)
    estado_fuentes: dict = field(default_factory=dict)   # entidad -> {"ok": bool, "detalle": str}
    cobertura: list[dict] = field(default_factory=list)  # [{entidad, cuenta, desde, hasta}] períodos de cada reporte
    advertencias: list[str] = field(default_factory=list)
    analisis: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)
