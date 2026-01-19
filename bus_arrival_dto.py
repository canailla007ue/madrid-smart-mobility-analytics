import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class BusArrivalDTO:
    """
    BusArrivalDTO - Datos enviados al tópico sobre una llegada de autobús.

    Campos:
    - line: Número o identificador de la línea.
    - stop: Identificador de la parada.
    - eta: Hora estimada de llegada (datetime, ISO 8601 en serialización).
    - distance: Distancia estimada hasta la parada en metros (si disponible).
    - estimate_arrive: Distancia estimada hasta la parada en metros (si disponible).
    - vehicle_id: Identificador del vehículo (si disponible).
    - destination: Destino mostrado por el vehículo (si disponible).
    - coords: Coordenadas GPS del vehículo (si disponible).
    - weather: Información meteorológica asociada (si disponible).
    - extra: Diccionario con campos adicionales libres.
    - sent_at: Marca temporal de envío (datetime, ISO 8601 en serialización).
    """

    line: str = field(metadata={"description": "Número o identificador de la línea"})
    stop: str = field(metadata={"description": "Identificador de la parada"})
    eta: Optional[datetime] = field(
        default=None, metadata={"description": "Hora estimada de llegada (datetime)"}
    )
    distance: Optional[int] = field(
        default=None,
        metadata={"description": "Distancia estimada hasta la parada en metros (si disponible)"}
    )
    estimate_arrive: Optional[int] = field(
        default=None,
        metadata={"description": "Distancia estimada hasta la parada en metros (si disponible)"}
    )
    vehicle_id: Optional[str] = field(
        default=None,
        metadata={"description": "Identificador del vehículo si disponible"},
    )
    destination: Optional[str] = field(
        default=None,
        metadata={"description": "Destino mostrado por el vehículo si disponible"},
    )
    coords: Optional[Dict[str, float]] = field(
        default=None,
        metadata={"description": "Coordenadas GPS del vehículo si disponible"},
    )
    weather: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "Información meteorológica asociada si disponible"},
    )
    extra: Dict[str, Any] = field(
        default_factory=dict, metadata={"description": "Campos adicionales arbitrarios"}
    )
    sent_at: Optional[datetime] = field(
        default=None, metadata={"description": "Marca temporal de envío (datetime)"}
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.eta:
            d["eta"] = self.eta.isoformat()
        if self.sent_at:
            d["sent_at"] = self.sent_at.isoformat()
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
