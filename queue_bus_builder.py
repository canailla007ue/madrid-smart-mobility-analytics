# python
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Union
from zoneinfo import ZoneInfo

from bus_arrival_builder import BusArrivalDTOBuilder
from bus_arrival_dto import BusArrivalDTO

SPAIN = ZoneInfo("Europe/Madrid")


def _parse_iso_datetime(s: Union[str, datetime, None]) -> Optional[datetime]:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s

    # Intentamos el formato estándar ISO primero (más rápido)
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        # Si falla, probamos formatos específicos
        formats = ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z")
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt)
            except (ValueError, TypeError):
                continue

    return None


def _ensure_spain_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SPAIN)
    return dt.astimezone(SPAIN)


def _set_sent_at(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("sent_at")
    if v is None:
        return
    dt = _parse_iso_datetime(v)
    if dt is not None:
        b.sent_at(_ensure_spain_tz(dt))


def _set_extra(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("extra")
    if v is not None:
        b.extra(v)


def _set_weather(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("weather")
    if v is not None:
        b.weather(v)


def _set_estimate_arrive(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("estimateArrive") if item.get("estimateArrive") else None
    if v is not None:
        b.estimate_arrive(v)  # deja que el builder valide la estructura


def _set_distance(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("DistanceBus") if item.get("DistanceBus") else None
    if v is not None:
        b.distance(v)  # deja que el builder valide la estructura


def _set_coords(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("geometry").get("coordinates") if item.get("geometry") else None
    if v is not None:
        b.coords(v)  # deja que el builder valide la estructura


def _set_destination(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("destination")
    if v is not None:
        b.destination(v)


def _set_vehicle_id(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("bus")
    if v is not None:
        b.vehicle_id(v)


def _set_eta(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("eta")
    if v is None:
        return
    dt = _parse_iso_datetime(v)
    if dt is not None:
        b.eta(_ensure_spain_tz(dt))


def _set_stop(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("stop")
    if v is not None:
        b.stop(v)


def _set_line(b: BusArrivalDTOBuilder, item: Dict[str, Any]) -> None:
    v = item.get("line")
    if v is not None:
        b.line(v)


class QueueBusBuilder:
    """
    Construye una cola (lista) de BusArrivalDTO.
    - add(item): acepta BusArrivalDTO o dict con claves compatibles con BusArrivalDTOBuilder.
    - from_iterable(iterable): añade muchos elementos.
    - build(): devuelve la lista de BusArrivalDTO.
    """
    def __init__(self):
        self._items: List[BusArrivalDTO] = []

    def add(self, item: Union[BusArrivalDTO, Dict[str, Any]]) -> "QueueBusBuilder":
        if isinstance(item, BusArrivalDTO):
            return self._add_dto(item)
        if isinstance(item, dict):
            return self._add_from_dict(item)
        raise ValueError("item debe ser BusArrivalDTO o dict compatible")

    def _add_dto(self, dto: BusArrivalDTO) -> "QueueBusBuilder":
        self._items.append(dto)
        return self

    def _add_from_dict(self, item: Dict[str, Any]) -> "QueueBusBuilder":
        b = BusArrivalDTOBuilder()
        # orden de handlers: primero obligatorios
        handlers = (
            _set_line,
            _set_stop,
            _set_eta,
            _set_vehicle_id,
            _set_destination,
            _set_coords,
            _set_weather,
            _set_distance,
            _set_extra,
            _set_estimate_arrive,
            _set_sent_at,
        )
        for h in handlers:
            h(b, item)
        dto = b.build()  # puede lanzar ValueError si faltan obligatorios
        self._items.append(dto)
        return self

    # --- handlers privados (cada uno muy simple) ---

    # --- resto de la clase ---
    def from_iterable(self, items: Iterable[Union[BusArrivalDTO, Dict[str, Any]]]) -> "QueueBusBuilder":
        for it in items:
            self.add(it)
        return self

    def build(self) -> List[BusArrivalDTO]:
        return list(self._items)