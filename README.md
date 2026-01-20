<div align="center">
  <h1 align="center">
    Madrid Smart Mobility Analytics
    <br />
    <br />
    <a href="https://github.com/canailla007ue/madrid-smart-mobility-analytics">
      <img src="./assets/slash-introducing.png" alt="Madrid Smart Mobility Analytics" width="100%">
    </a>
  </h1>
</div>
<p align="center">
<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python"/>
  <img src="https://img.shields.io/badge/Rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ"/>
  <img src="https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Apache%20Spark-FDEE21?style=for-the-badge&logo=apachespark&logoColor=black" alt="Apache Spark"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>

  <br/>

  <img src="https://img.shields.io/badge/Code%20Style-PEP8-black?style=flat" alt="PEP8"/>
  <img src="https://img.shields.io/badge/Estado-En_Desarrollo-yellow?style=flat" alt="Estado"/>
  <img src="https://img.shields.io/github/license/canailla007ue/madrid-smart-mobility-analytics?style=flat" alt="Licencia"/>
  </p>
<p align="center">
  <a href="https://www.youtube.com/watch?v=tgLBHhQNBlE">
    <img src="https://img.youtube.com/vi/tgLBHhQNBlE/hqdefault.jpg" alt="Video TFG" width="700">
  </a>
*Haz clic en la imagen de arriba para ver el video explicativo de la arquitectura.*

</p>

## Introducción

[ Madrid Smart Mobility Analytics] este proyecto implementa una arquitectura backend asíncrona diseñada para desacoplar la ingesta de datos del procesamiento intensivo. El objetivo principal es eliminar los tiempos de espera (latencia) en las respuestas de la API y garantizar la integridad de los datos bajo alta carga.

El flujo de trabajo sigue un patrón Productor-Consumidor optimizado:

- **Procesamiento Asíncrono (Non-blocking I/O)**

> Para evitar cuellos de botella en la API, las peticiones entrantes no se procesan en tiempo real. En su lugar, el sistema encola inmediatamente la tarea en **RabbitMQ** y libera la conexión con el cliente. Esto reduce el tiempo de respuesta de la API a milisegundos, independientemente de la complejidad del cálculo posterior.

- **Escalabilidad Horizontal de Workers**

> El consumo de mensajes es gestionado por scripts de **Python** independientes. Esta arquitectura permite optimizar el uso de recursos: si la cola crece, se pueden instanciar dinámicamente más workers para aumentar la velocidad de procesamiento en paralelo sin modificar el código base ni detener el servicio.

- **Persistencia de Alto Rendimiento**

> Los resultados procesados se vuelcan de forma asíncrona en **MongoDB**. Al utilizar un modelo de documentos (JSON), evitamos el overhead de transformaciones complejas (ORM) y optimizamos la velocidad de escritura (write throughput), necesaria cuando los workers procesan grandes volúmenes de mensajes simultáneamente.

## Estructura del Código

El proyecto está modularizado siguiendo el principio de responsabilidad única (SRP).

### 📡 Clientes de API (`/src`)
La lógica de conexión está encapsulada en clases dedicadas con manejo de errores y logging:

* **`emt.py` (Clase `EMTClient`)**:
    * Gestiona la autenticación (Token refresh) con la API de la EMT.
    * Obtiene tiempos de llegada y posicionamiento de autobuses.
    
* **`aemet.py` (Clase `AEMETClient`)**:
    * Interactúa con la API OpenData de AEMET.
    * Normaliza datos meteorológicos para cruzarlos con el estado del tráfico.

### ⚙️ Orquestación
* **`main.py`**:
    * Punto de entrada del ingestor.
    * Orquesta las llamadas a los clientes y gestiona el ciclo de vida del productor de RabbitMQ.
    * Implementa un sistema de **Logging Centralizado** configurable, sustituyendo las salidas estándar por logs estructurados para producción.

---

## Configuración e Instalación

### 1. Requisitos Previos
* Python 3.8+
* Instancias de RabbitMQ y MongoDB (local o Docker).

### 2. Instalación de Dependencias
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### Arquitectura del Sistema

<div align="center">
  <img src="./assets/arquitectura.svg" alt="Diagrama de Arquitectura del Sistema" width="80%">
</div>


# Documentación

## APIs
- [AEMET OpenData: Acceso y documentación de API REST](https://opendata.aemet.es/dist/index.html)

- [Documentación técnica de la API Open Data (Swagger UI) - Mobility Labs](https://datos.emtmadrid.es/m360-swagger/docs)
