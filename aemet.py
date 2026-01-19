# File: `aemet.py`
import logging
import os
from typing import Optional, Any
import requests

_logger = logging.getLogger(__name__)


def get_weather(datos_url: str, timeout: int = 10, logger: Optional[logging.Logger] = None) -> Any:
    """
    Descarga y devuelve el JSON de la URL `datos_url`.
    Lanza requests.RequestException en errores de conexión y RuntimeError si la respuesta no es JSON.
    """
    logger = logger or _logger

    if not datos_url:
        logger.error("❌ No se proporcionó 'datos_url'. La API de AEMET no devolvió una URL válida.")
        return None

    try:
        logger.info(f"🌍 URL intermedia obtenida: {datos_url}")

        # SEGUNDA PETICIÓN: Vamos a buscar los datos reales a esa URL
        respuesta_final = requests.get(datos_url, timeout=timeout)

        if respuesta_final.status_code == 200:
            # AEMET a veces devuelve la codificación en 'latin-1'
            respuesta_final.encoding = 'latin-1'
            datos_climaticos = respuesta_final.json()

            logger.info("✅ Datos climáticos descargados correctamente.")
            logger.debug(f"Payload recibido: {datos_climaticos}")
            return datos_climaticos

        else:
            logger.error(f"❌ Error al descargar los datos finales: HTTP {respuesta_final.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"💥 Error de conexión al obtener datos finales de AEMET: {e}")
        return None
    except ValueError:
        logger.error("💥 La respuesta final de AEMET no es un JSON válido.")
        return None


class AEMETClient:
    AEMET_BASE = "https://opendata.aemet.es/opendata/api/observacion/convencional/datos/estacion"

    def __init__(
            self,
            api_key: Optional[str] = None,
            station_id: str = "3195",
            timeout: int = 10,
            logger: Optional[logging.Logger] = None,
    ) -> None:
        # Priorizar la API key pasada por argumento, si no, buscar en entorno
        self.api_key = api_key or os.getenv("API_KEY")
        self.station_id = station_id
        self.timeout = timeout
        self.logger = logger or _logger

        if not self.api_key:
            self.logger.error("Falta AEMET_API_KEY")
            raise ValueError("Falta api_key: configura `AEMET_API_KEY` o pásala al crear AEMETClient.")

    def get_aemet_datos_url(self, timeout: int = 10) -> Any:
        """
        Llama al endpoint de AEMET para la estación y delega en get_weather para obtener el JSON final.
        """
        url = f"{self.AEMET_BASE}/{self.station_id}"
        headers = {
            "accept": "application/json",
            "api_key": self.api_key,
            "User-Agent": "TFG-Bus-Weather-Monitor-Madrid/1.0 (Contact: canailla007@gmail.com)"
        }

        try:
            self.logger.info(f"📡 Solicitando URL de datos para estación: {self.station_id}")
            resp = requests.get(url, headers=headers, timeout=timeout or self.timeout)
            resp.raise_for_status()

            payload = resp.json()

            # Extraemos la URL donde están los datos reales (campo 'datos')
            datos_url = payload.get("datos")

            # Llamamos a la función auxiliar para bajar el JSON real
            return get_weather(datos_url, timeout=timeout, logger=self.logger)

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"❌ Error HTTP en la petición inicial a AEMET: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error inesperado en AEMETClient: {e}")
            return None
