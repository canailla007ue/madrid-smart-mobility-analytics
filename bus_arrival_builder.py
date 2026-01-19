# python
from datetime import datetime
from typing import Any, Dict, Optional,Sequence
from zoneinfo import ZoneInfo

from bus_arrival_dto import BusArrivalDTO

SPAIN = ZoneInfo("Europe/Madrid")


def _ensure_spain_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SPAIN)
    return dt.astimezone(SPAIN)


class BusArrivalDTOBuilder:
    def __init__(self):
        self._line: Optional[str] = None
        self._stop: Optional[str] = None
        self._eta: Optional[datetime] = None
        self._vehicle_id: Optional[str] = None
        self._destination: Optional[str] = None
        self._coords: Optional[Dict[str, float]] = None
        self._weather: Optional[Dict[str, Any]] = None
        self._distance: Optional[int] = None
        self._estimate_arrive: Optional[int] = None
        self._extra: Dict[str, Any] = {}
        self._sent_at: Optional[datetime] = None

    def line(self, line: str) -> "BusArrivalDTOBuilder":
        self._line = line
        return self

    def distance(self, distance: int) -> "BusArrivalDTOBuilder":
        """Establece la distancia en metros hasta la parada."""
        if distance is not None:
            self._distance = int(distance)
        return self

    def estimate_arrive(self, estimate_arrive: int) -> "BusArrivalDTOBuilder":
        """Establece la distancia estimada en metros hasta la parada."""
        if estimate_arrive is not None:
            self._estimate_arrive = int(estimate_arrive)
        return self

    def stop(self, stop: str) -> "BusArrivalDTOBuilder":
        self._stop = stop
        return self

    def eta(self, eta: datetime) -> "BusArrivalDTOBuilder":
        self._eta = eta
        return self

    def vehicle_id(self, vehicle_id: str) -> "BusArrivalDTOBuilder":
        self._vehicle_id = vehicle_id
        return self

    def destination(self, destination: str) -> "BusArrivalDTOBuilder":
        self._destination = destination
        return self

    def coords(self, coords: Sequence[float]) -> "BusArrivalDTOBuilder":
        if isinstance(coords, Sequence) and not isinstance(coords, (str, bytes)) and len(coords) >= 2:
            try:
                first = float(coords[0])
                second = float(coords[1])
            except Exception:
                raise ValueError("coords debe ser secuencia numérica de dos elementos")
            # Convención: asumir GeoJSON [lon, lat] => lon=first, lat=second
            lon = first
            lat = second
            # pequeña validación de rango
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                raise ValueError("valores de lat/lon fuera de rango esperado")
            self._coords = {"lat": lat, "lon": lon}
            return self

        raise ValueError("coords debe ser dict con 'lat'/'lon' o secuencia [lon, lat]")

    def weather(self, weather: Dict[str, Any]) -> "BusArrivalDTOBuilder":
        self._weather = weather
        return self

    def extra(self, extra: Dict[str, Any]) -> "BusArrivalDTOBuilder":
        self._extra = extra
        return self

    def sent_at(self, sent_at: datetime) -> "BusArrivalDTOBuilder":
        self._sent_at = sent_at
        return self

    def build(self) -> BusArrivalDTO:
        if not self._line or not self._stop:
            raise ValueError("Campos obligatorios: line y stop")

        if self._sent_at is None:
            sent = datetime.now(SPAIN)
        else:
            sent = _ensure_spain_tz(self._sent_at)

        eta = _ensure_spain_tz(self._eta) if self._eta is not None else None

        return BusArrivalDTO(
            line=self._line,
            stop=self._stop,
            eta=eta,
            vehicle_id=self._vehicle_id,
            destination=self._destination,
            coords=self._coords,
            weather=self._weather,
            distance=self._distance,
            estimate_arrive=self._estimate_arrive,
            extra=self._extra,
            sent_at=sent,
        )
