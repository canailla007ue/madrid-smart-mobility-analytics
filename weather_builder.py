
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

SPAIN = ZoneInfo("Europe/Madrid")

def _ensure_spain_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SPAIN)
    return dt.astimezone(SPAIN)


def _has_relevant_keys(aemet: Dict[str, Any]) -> bool:
    # Ahora buscamos ta (temp), hr (humedad), vv (viento), prec (lluvia) o fint (fecha)
    return any(k in aemet for k in ("ta", "hr", "vv", "prec", "fint"))

class WeatherBuilder:
    def __init__(self):
        self._weather: Dict[str, Any] = {}

    def from_aemet(self, aemet: Dict[str, Any]) -> "WeatherBuilder":
        if not isinstance(aemet, dict):
            raise ValueError("aemet debe ser un dict")

        if not _has_relevant_keys(aemet):
            return self

        self._extract_temp(aemet)
        self._extract_humidity(aemet)
        self._extract_wind_speed(aemet)
        self._extract_precipitation(aemet)
        self._extract_observed_at(aemet)

        return self

    def build(self) -> Dict[str, Any]:
        return dict(self._weather)

    def _extract_temp(self, aemet: Dict[str, Any]) -> None:
        exist_and_not_is_none_temp = "ta" in aemet and aemet["ta"] is not None
        if exist_and_not_is_none_temp:
            self._weather["temperature"] = aemet["ta"]

    def _extract_humidity(self, aemet: Dict[str, Any]) -> None:
        exist_and_not_is_none_humidity = "hr" in aemet and aemet["hr"] is not None
        if exist_and_not_is_none_humidity:
            self._weather["humidity"] = aemet["hr"]

    def _extract_wind_speed(self, aemet: Dict[str, Any]) -> None:
        wind = aemet.get("vv")
        exist_and_not_is_none_wind_vel = isinstance(wind, dict) and "vv" in wind and wind["vv"] is not None
        exist_and_not_is_none_vel_top = "vv" in aemet and aemet["vv"] is not None
        if exist_and_not_is_none_wind_vel:
            self._weather["wind_speed"] = wind["vv"]
        elif exist_and_not_is_none_vel_top:
            self._weather["wind_speed"] = aemet["vv"]

    def _extract_precipitation(self, aemet: Dict[str, Any]) -> None:
        # solo actúa si la clave 'prec' existe
        if "prec" not in aemet or aemet["prec"] is None:
            return
        raw = aemet["prec"]

        # si ya es número, lo guardamos y calculamos is_raining
        if isinstance(raw, (int, float)):
            num = float(raw)
            self._weather["precipitation"] = num
            self._weather["is_raining"] = num > 0.0
            return

        # si existe pero no es número, guardamos el valor crudo (sin intentar parsear)
        self._weather["precipitation"] = raw

    def _extract_observed_at(self, aemet: Dict[str, Any]) -> None:
        # AEMET usa 'fint' para la fecha de fin de observación (ISO 8601)
        fecha_raw = aemet.get("fint")

        if not fecha_raw:
            return

        try:
            # Intentamos parsear la fecha estándar
            observed_dt = datetime.fromisoformat(fecha_raw)
            # Aseguramos zona horaria y guardamos en ISO
            self._weather["observed_at"] = _ensure_spain_tz(observed_dt).isoformat()
        except (ValueError, TypeError):
            # Si el formato es extraño, guardamos el string original como fallback
            # Capturamos solo errores de valor o tipo de dato
            self._weather["observed_at"] = fecha_raw