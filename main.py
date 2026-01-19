
# python
import json
import logging
import os
import time
from typing import Callable, Any

from requests import HTTPError

from aemet import AEMETClient
from emt import EMTClient
from bus_arrival_builder import BusArrivalDTOBuilder
from weather_builder import WeatherBuilder
from queue_bus_builder import QueueBusBuilder
from rabbit_publisher import RabbitPublisher

builder = BusArrivalDTOBuilder()

def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    return logging.getLogger("app")


logger = setup_logging()


def _get_wait_time(response: Any, attempt: int, backoff_factor: float) -> int:
    """Calcula el tiempo de espera basado en headers o backoff exponencial."""
    retry_after = response.headers.get("Retry-After") if response else None

    if retry_after and retry_after.isdigit():
        return int(retry_after)

    return int(backoff_factor ** attempt)


def retry_on_http_429(func: Callable[[], Any], *, max_attempts: int = 5, backoff_factor: float = 2.0):
    """
    Ejecuta `func` y reintenta específicamente ante errores HTTP 429.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except HTTPError as e:
            response = getattr(e, "response", None)

            # Si no es 429, registramos y relanzamos inmediatamente
            if response is None or response.status_code != 429:
                logger.error("HTTPError no gestionable (no 429) en intento %d", attempt)
                raise e

            # Es un 429: calculamos espera y reintentamos
            wait = _get_wait_time(response, attempt, backoff_factor)
            logger.warning("HTTP 429 (Rate Limit). Reintento %d/%d: esperando %ds",
                           attempt, max_attempts, wait)
            time.sleep(wait)

        except Exception as e:
            logger.exception("Error crítico no recuperable en intento %d", attempt)
            raise e

    raise RuntimeError(f"Máximo de intentos ({max_attempts}) alcanzado para la API")


def group_by_line(bus_list, weather):
    grouped = {}
    for b in bus_list:
        line = b.get("line")
        destination = b.get("destination")
        # La clave es la combinación de ambos
        key = (line, destination)

        entry = {
            "line": line,
            "destination": destination,
            "stop": b.get("stop"),
            "estimateArrive": b.get("estimateArrive"),
            "vehicle_id": b.get("bus"),
            "coords": {
                "lat": b.get("geometry", {}).get("coordinates", [None, None])[1],
                "lon": b.get("geometry", {}).get("coordinates", [None, None])[0],
            },
            "weather": weather,
        }
        grouped.setdefault(key, []).append(entry)

    # Al retornar, mantenemos line y destination en la raíz del objeto
    return [{"line": k[0], "destination": k[1], "stops": v} for k, v in grouped.items()]


def get_all_bus_data(stops):
    """
    Recupera y agrega los datos de todas las paradas especificadas.
    """
    emt = EMTClient()
    all_buses = []

    for stop in stops:
        logger.info(f"[*] Consultando parada: {stop}")

        try:
            buses_in_stop = emt.lines_bus_stop(stop)

            # Si la API devuelve None o lista vacía, saltamos a la siguiente
            if not buses_in_stop:
                logger.warning(f"La parada {stop} no devolvió datos (posiblemente sin servicio).")
                continue

            # Procesamos y enriquecemos cada bus
            for bus in buses_in_stop:
                bus['origin_stop'] = stop

            all_buses.extend(buses_in_stop)

        except (RuntimeError, ValueError) as e:
            # Capturamos errores específicos de la API o de formato
            logger.error(f"Error controlado en parada {stop}: {e}")
            continue
        except Exception as e:
            # Solo capturamos Exception aquí para evitar que el programa muera,
            # pero registrando el tipo específico para depuración.
            logger.critical(f"Error inesperado procesando parada {stop}: {type(e).__name__} - {e}")
            continue

    return all_buses

def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO")) # requiere AEMET_API_KEY en entorno
    # Instanciar correctamente pasando la api_key como keyword argument

    weather_dict=get_weather()



    # Obtener datos y manejarlos de forma segura
    try:

        paradas_objetivo = ["5907", "66", "5427","5428","65","5907","1049","2002"]
        autobuses_queue = get_all_bus_data(paradas_objetivo)
        
        queue_builder = QueueBusBuilder()
        queue_builder.from_iterable(autobuses_queue)
        queue = queue_builder.build()

        # Mostrar resultados
        for i, arrival in enumerate(queue, start=1):
            print(f"{i}: {arrival}")

        mail_body = (
            f"Temperatura: {weather_dict.get('temperature', 'N/A')}\n"
            f"Velocidad Viento: {weather_dict.get('wind_speed', 'N/A')}\n"
            f"Fecha: {weather_dict.get('observed_at', 'N/A')}\n"
            f"Precipitation: {weather_dict.get('precipitation', 'N/A')}\n"

        )

        print(mail_body)
        payload = group_by_line(autobuses_queue,  weather_dict)
        with RabbitPublisher() as pub:
            success = pub.publish(payload)
            if not success:
                logger.error("Fallo al enviar payload a la cola")
            else:
                logger.info("Payload enviado correctamente a la cola")

        # imprimir antes de enviar
        print("Payload a enviar:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception:
        logger.exception("Error al obtener datos de AEMET")
        return


def get_weather():
    try:
        # Intentamos obtener los datos con tu lógica de reintentos
        datos = retry_on_http_429(lambda: AEMETClient().get_aemet_datos_url())

        # Si datos es válido, construimos el diccionario
        if datos and len(datos) > 0:
            return WeatherBuilder().from_aemet(datos[-1]).build()
        else:
            raise ValueError("Datos de AEMET vacíos")

    except Exception as e:
        # Logueamos el error para saber qué pasó, pero no cortamos la ejecución
        logger.error(f"Error al obtener clima, marcando como PENDING: {e}")
        return {
            "status": "PENDING",
            "temp": None,
            "precip": None,
            "error_log": str(e)  # Opcional: para saber por qué falló luego
        }


if __name__ == "__main__":
    main()
