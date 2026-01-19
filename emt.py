# python
"""
Cliente para la API de EMT Madrid.

Este módulo proporciona la clase `EMTClient` para obtener un token de acceso y
consultar las llegadas de autobuses en una parada determinada.

Variables de entorno utilizadas (opcional):
- EMT_CLIENT_ID
- EMT_PASSWORD
"""

import json
import os
from typing import Any, Dict, Optional

import requests

LOGIN_URL = "https://datos.emtmadrid.es/v3/mobilitylabs/user/login/"


class EMTClient:
    """
    Cliente para la API de EMT Madrid.

    Args:
       timeout (int): Tiempo de espera en segundos para las peticiones HTTP.

    Attributes:
        client_id (Optional[str]): Identificador usado.
        password (Optional[str]): Contraseña usada.
        timeout (int): Tiempo de espera para peticiones.
        token (Optional[str]): Token de acceso obtenido tras autenticación.
    """

    def __init__(
        self,
        timeout: int = 60,
    ):
        self.client_id = os.getenv("EMT_CLIENT_ID")
        self.password = os.getenv("EMT_PASSWORD")
        self.timeout = timeout
        self.token: Optional[str] = None

    def get_token(self) -> str:
        """
        Solicita y devuelve el token de acceso a la API de EMT.

        Returns:
            str: Token de acceso.

        Raises:
            ValueError: Si faltan las credenciales.
            RuntimeError: Si la respuesta no es JSON, el formato es inesperado o
                la API responde con error.
        """
        if not self.client_id or not self.password:
            raise ValueError(
                "Faltan credenciales: configura `EMT_CLIENT_ID` y `EMT_PASSWORD` en el entorno."
            )
        headers = {"email": self.client_id, "password": self.password}
        resp = requests.get(LOGIN_URL, headers=headers, timeout=self.timeout)
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(
                f"Respuesta no JSON (HTTP {resp.status_code}): {resp.text}"
            )
        if resp.status_code == 200 and data.get("code") in {"00", "01"}:
            lst = data.get("data")
            if isinstance(lst, list) and lst and "accessToken" in lst[0]:
                self.token = lst[0]["accessToken"]
                return self.token
            raise RuntimeError("Formato de respuesta inesperado: falta accessToken.")
        raise RuntimeError(f"Error al obtener token: {data.get('description') or data}")

    def ensure_token(self) -> str:
        """
        Asegura que existe un token válido en memoria; si no, lo solicita.

        Returns:
            str: Token de acceso.

        Raises:
            Verifica las mismas condiciones que `get_token`.
        """
        if not self.token:
            return self.get_token()
        return self.token

    def lines_bus_stop(self, stop_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la lista de llegadas para una parada de autobús.

        Args:
            stop_id (str): Identificador de la parada EMT.

        Returns:
            Optional[Dict[str, Any]]: Bloque de llegadas (`Arrive`) tal como lo
            devuelve la API, para ser procesado por el caller.
        """
        token = self.ensure_token()
        url = f"https://openapi.emtmadrid.es/v2/transport/busemtmad/stops/{stop_id}/arrives/"
        headers = {"accessToken": token, "Content-Type": "application/json"}
        payload = {
            "cultureInfo": "ES",
            "Text_StopRequired_YN": "Y",
            "Text_EstimationsRequired_YN": "Y",
            "Text_IncidencesRequired_YN": "N",
            "DateTime_Referenced_Incidencies_YYYYMMDD": "20260117",
        }
        resp = requests.post(
            url, headers=headers, data=json.dumps(payload), timeout=self.timeout
        )
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"Respuesta no JSON (HTTP {resp.status_code})")
        if resp.status_code != 200:
            raise RuntimeError(f"Error HTTP {resp.status_code}: {resp.text}")
        if data.get("code") not in {"00", "01"}:
            raise RuntimeError(
                f"La API respondió con error: {data.get('description') or data}"
            )
        try:
            return data["data"][0]["Arrive"]
        except Exception:
            raise RuntimeError("Formato inesperado en la respuesta de llegadas.")
