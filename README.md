# Bot de Encuesta UPTC — Chatbots Conversacionales vs. Formularios Tradicionales

Bot de Telegram desarrollado en Python para la recolección de datos del cuasi-experimento académico **"Chatbots conversacionales vs. Formularios tradicionales en la UPTC"**, realizado en la Escuela de Ingeniería de Sistemas y Computación de la Universidad Pedagógica y Tecnológica de Colombia (UPTC), sede Tunja.

## Autores

* Edwin David Fino Velandia
* Edward Mauricio Guatibonza Suárez
* Fredy Alejandro Bonilla Rodríguez

---

## Características principales

* **Flujo conversacional guiado:** Consentimiento informado inicial y cuestionario de 20 preguntas (9 cerradas, 1 abierta opcional y 10 ítems de la escala de usabilidad SUS).
* **Navegación bidireccional:** Botones `⬅️ Anterior` y `Siguiente ➡️` (habilitado solo cuando la pregunta ya fue respondida) con indicador visual `✓` de la respuesta previa para reducir la deserción sin comprometer la integridad del instrumento.
* **Anonimización de participantes:** Los IDs de Telegram se anonimizan mediante HMAC-SHA256 usando una clave secreta (`HASH_SECRET`).
* **Métricas automáticas:** Registro de tiempos de inicio/fin, duración en segundos, estado de finalización (`completado`, `cancel`, `timeout`, `reinicio`), punto exacto de abandono (`P1`–`P20`) y cálculo automático del puntaje **SUS (0–100)**.
* **Persistencia segura:** Escritura atómica en CSV (`resultados_telegram.csv`) con bloqueo asíncrono (`asyncio.Lock`) y soporte para volumen persistente en Railway.
* **Exportación a Excel (`/exportar`):** Genera y envía por Telegram un archivo `.xlsx` formateado con dos pestañas:
  * **Respuestas:** Encabezados multilínea agrupados por color, filtros automáticos y resaltado de encuestas completadas/abandonadas.
  * **Resumen:** Indicadores clave calculados con fórmulas automáticas (intentos totales, completadas, abandonadas, tasa de finalización, duración promedio y puntaje SUS promedio).

---

## Estructura del proyecto

```text
BotTelegram/
├── bot_encuesta.py        # Lógica principal del bot, flujo de conversación y persistencia CSV
├── cuestionario.py        # Definición de preguntas, opciones, textos y columnas SUS
├── exportador_excel.py    # Conversión del CSV a archivo Excel (.xlsx) con formato y resumen
├── requirements.txt       # Dependencias de Python
└── README.md              # Documentación del proyecto
```

---

## Requisitos previos

* Python 3.10 o superior
* Token de bot de Telegram (obtenido mediante `@BotFather`)

---

## Configuración e instalación local

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/davidfino1/bot-encuesta-uptc.git](https://github.com/davidfino1/bot-encuesta-uptc.git)
   cd bot-encuesta-uptc
   ```

2. **Crear y activar un entorno virtual (opcional pero recomendado):**
   ```bash
   python -m venv .venv
   # En Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # En Linux / macOS:
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto (este archivo no se sube a GitHub) con las siguientes variables:

   ```env
   TELEGRAM_BOT_TOKEN=tu_token_de_botfather
   HASH_SECRET=clave_secreta_para_anonimizacion
   ADMIN_USER_ID=7662539873,otro_id_opcional
   DATA_DIR=.
   ```

   | Variable | Descripción |
   | :--- | :--- |
   | `TELEGRAM_BOT_TOKEN` | Token del bot entregado por `@BotFather`. |
   | `HASH_SECRET` | Clave secreta para generar el hash HMAC-SHA256 del participante. |
   | `ADMIN_USER_ID` | Uno o varios IDs numéricos de Telegram separados por coma con permiso para usar `/exportar`. |
   | `DATA_DIR` | Carpeta donde se guarda `resultados_telegram.csv` (en Railway apunta al volumen, ej. `/data`). |

5. **Ejecutar el bot:**
   ```bash
   python bot_encuesta.py
   ```

> **Importante:** No ejecutes el bot de forma local con el mismo `TELEGRAM_BOT_TOKEN` mientras la instancia en Railway esté activa. Telegram solo permite una conexión de *polling* por token y generará un error `409 Conflict`.

---

## Comandos del bot

* `/start` — Inicia la encuesta desde el consentimiento informado.
* `/cancel` — Cancela la encuesta en curso y registra el abandono.
* `/exportar` — *(Solo administradores)* Genera y envía el archivo `resultados_encuesta_uptc.xlsx`.

---

## Despliegue en Railway

El proyecto está configurado para desplegarse automáticamente en **Railway** desde la rama `main`:

1. Conectar el repositorio `davidfino1/bot-encuesta-uptc` en Railway.
2. Agregar un **Volume** montado en `/data` para conservar los resultados entre despliegues.
3. Configurar las variables de entorno `TELEGRAM_BOT_TOKEN`, `HASH_SECRET`, `ADMIN_USER_ID` y `DATA_DIR=/data`.
4. Cada `git push` a `main` reconstruye y reinicia el servicio automáticamente.