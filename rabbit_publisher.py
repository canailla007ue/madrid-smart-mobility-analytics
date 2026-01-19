import json
import logging
import os
import time
from typing import Any, Optional
import pika
# Importamos excepciones específicas de Pika para manejarlas mejor
from pika.exceptions import AMQPConnectionError, AMQPChannelError


class RabbitPublisher:
    """
    Publicador robusto a RabbitMQ con Publisher Confirms y reconexión automática.
    """

    def __init__(
            self,
            logger: Optional[logging.Logger] = None,
            durable: bool = True
    ):

        env_user = os.getenv("RABBITMQ_USER")
        env_pass = os.getenv("RABBITMQ_PASS")
        env_host = os.getenv("RABBITMQ_HOST")
        self.url = f"amqps://{env_user}:{env_pass}@{env_host}"
        self.queue = "micola_queue"
        self.logger = logger or logging.getLogger(__name__)
        self.durable = durable

        # Guardamos los parámetros pero NO conectamos en el __init__
        # para facilitar la reconexión en caso de fallo.
        if not self.url or not self.queue:
            raise ValueError("Faltan RABBIT_URL o RABBIT_QUEUE")

        self._params = pika.URLParameters(self.url)
        self._connection = None
        self._channel = None

    def _connect(self):
        """Método interno para establecer conexión y canal."""
        if not self._connection or self._connection.is_closed:
            self.logger.info("Conectando a RabbitMQ...")
            self._connection = pika.BlockingConnection(self._params)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self.queue, durable=self.durable)

            # --- MEJORA CRÍTICA: Publisher Confirms ---
            # Esto le dice a RabbitMQ: "Avísame cuando hayas guardado el mensaje"
            self._channel.confirm_delivery()
            self.logger.info("Conexión establecida y Confirms activados.")

    def publish(self, payload: Any, retries: int = 3) -> bool:
        """
        Publica con reintentos y confirmación de entrega.
        Retorna True si el mensaje fue confirmado por el broker.
        """
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        # Propiedades estáticas (Persistencia)
        props = pika.BasicProperties(content_type="application/json", delivery_mode=2)

        for attempt in range(1, retries + 1):
            try:
                self._connect()  # Asegura que estamos conectados

                # Al tener confirm_delivery activado, basic_publish puede lanzar excepciones
                # si el mensaje no se puede enrutar, garantizando seguridad.
                self._channel.basic_publish(
                    exchange="",
                    routing_key=self.queue,
                    body=body,
                    properties=props,
                    mandatory=True  # Lanza error si no se puede enrutar
                )

                self.logger.debug("Mensaje publicado y confirmado en %s", self.queue)
                return True

            except (AMQPConnectionError, AMQPChannelError) as e:
                self.logger.warning(f"Error de conexión (intento {attempt}/{retries}): {e}")
                self._connection = None  # Forzamos reconexión en la siguiente vuelta
                time.sleep(2)  # Espera antes de reintentar
            except Exception as e:
                self.logger.error(f"Error irrecuperable publicando: {e}")
                raise e

        self.logger.error("Fallo al publicar mensaje después de todos los reintentos.")
        return False

    def close(self):
        """Cierra la conexión de RabbitMQ de forma segura."""
        try:
            # Verificamos si existe la conexión y si no está ya cerrada
            if hasattr(self, '_connection') and self._connection and self._connection.is_open:
                self._connection.close()
                self.logger.info("Conexión con RabbitMQ cerrada correctamente.")
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError) as e:
            self.logger.warning("La conexión ya estaba cerrada o hubo un error de protocolo al cerrar: %s", e)
        except Exception as e:
            # Aquí sí es útil un log de error porque es algo totalmente imprevisto
            self.logger.error("Error inesperado de tipo %s al cerrar RabbitMQ: %s", type(e).__name__, e)

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()