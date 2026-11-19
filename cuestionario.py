TEXT_QUESTION_TYPE = "text"
SCALE_OPTIONS = ["1", "2", "3", "4", "5"]
SCALE_COLUMNS = 5
SEMESTER_COUNT = 10
SEMESTER_COLUMNS = 5
SUS_FIRST_POSITION = 10
SUS_LAST_POSITION = 20

AGREEMENT_HINT = "1 = Completamente en desacuerdo, 5 = Completamente de acuerdo"

CONSENT_TEXT = (
    "AVISO DE PRIVACIDAD Y CONSENTIMIENTO INFORMADO\n\n"
    "Esta encuesta es voluntaria. Tus respuestas se usarán solo con fines académicos "
    "y de forma anónima, en un proyecto de Metodología de la Investigación de la UPTC "
    "que compara canales de recolección de información.\n\n"
    "• Puedes retirarte en cualquier momento con /cancel.\n"
    "• No se guardan tu nombre, tu usuario ni tu ID de Telegram; solo un código "
    "irreversible (hash) que impide identificarte.\n"
    "• Tienes derecho a conocer, actualizar y solicitar la supresión de tus datos "
    "(Ley 1581 de 2012). Contacto: edwin.fino@uptc.edu.co.\n\n"
    "¿Autorizas el tratamiento de tus datos en estos términos?"
)

ACCEPT_LABEL = "Acepto voluntariamente"
REJECT_LABEL = "Rechazo"
SKIP_LABEL = "Omitir"
REJECTED_TEXT = "Entendido, no se registró ningún dato. Gracias por tu tiempo."
THANKS_TEXT = "¡Gracias por tu participación! Tus respuestas fueron registradas."
CANCELLED_TEXT = "Encuesta cancelada. Gracias por tu tiempo. Escribe /start si quieres empezar de nuevo."
TIMEOUT_TEXT = "La sesión expiró por inactividad. Escribe /start si quieres empezar de nuevo."
USE_BUTTONS_TEXT = "Por favor usa los botones para responder, o /cancel para salir."
NO_ACTIVE_SURVEY_TEXT = "No hay una encuesta activa. Escribe /start para comenzar."
EXPIRED_SURVEY_TEXT = "Esta encuesta ya no está activa. Escribe /start."
MISSING_SETTINGS_TEXT = "Faltan TELEGRAM_BOT_TOKEN o HASH_SECRET en el archivo .env"


def likert(column, text, hint=AGREEMENT_HINT):
    return {
        "column": column,
        "text": f"{text}\n({hint})",
        "options": SCALE_OPTIONS,
        "columns": SCALE_COLUMNS,
    }


QUESTIONS = [
    {
        "column": "q01_semestre",
        "text": "¿En qué semestre estás?",
        "options": [str(number) for number in range(1, SEMESTER_COUNT + 1)],
        "columns": SEMESTER_COLUMNS,
    },
    {
        "column": "q02_facultad",
        "text": "¿A qué facultad perteneces?",
        "options": [
            "Ciencias de la Educación",
            "Ciencias Agropecuarias",
            "Ingeniería",
            "Ciencias Económicas y Administrativas",
            "Ciencias Básicas",
            "Derecho y Ciencias Sociales",
            "Ciencias de la Salud",
            "Estudios a Distancia",
            "Otra",
        ],
        "columns": 1,
    },
    {
        "column": "q03_dispositivo",
        "text": "¿Desde qué dispositivo estás respondiendo?",
        "options": ["Celular", "Computador", "Tablet"],
        "columns": 3,
    },
    {
        "column": "q04_uso_telegram",
        "text": "¿Con qué frecuencia usas Telegram?",
        "options": ["Nunca", "Ocasionalmente", "Semanalmente", "A diario"],
        "columns": 2,
    },
    {
        "column": "q05_frecuencia_encuestas",
        "text": "¿Con qué frecuencia respondes encuestas (institucionales, académicas o de otro tipo)?",
        "options": ["Nunca", "Rara vez", "A veces", "Frecuentemente"],
        "columns": 2,
    },
    likert(
        "q06_disposicion",
        "En general, ¿qué tan dispuesto/a estás a responder encuestas de la universidad?",
        "1 = Nada dispuesto/a, 5 = Muy dispuesto/a",
    ),
    {
        "column": "q07_motivo_abandono_encuestas",
        "text": "¿Qué te hace dejar una encuesta sin terminar?",
        "options": [
            "Es muy larga",
            "Preguntas repetitivas o confusas",
            "No me interesa el tema",
            "Falta de tiempo",
            "Problemas técnicos",
            "Nunca dejo encuestas sin terminar",
            "Otro",
        ],
        "columns": 1,
    },
    likert(
        "q08_encuestas_faciles",
        "Las encuestas que recibo de la universidad son fáciles de responder.",
        "1 = Totalmente en desacuerdo, 5 = Totalmente de acuerdo",
    ),
    {
        "column": "q09_medio_preferido",
        "text": "¿Por qué medio preferirías recibir las encuestas institucionales?",
        "options": [
            "Correo institucional",
            "WhatsApp",
            "Telegram",
            "Plataforma web de la universidad",
            "Redes sociales",
            "Otro",
        ],
        "columns": 2,
    },
    {
        "column": "q10_sugerencia",
        "text": "¿Qué cambiarías para que más estudiantes respondan las encuestas de la universidad? (opcional)\n\nEscríbelo en un mensaje o pulsa Omitir.",
        "type": TEXT_QUESTION_TYPE,
    },
    likert(
        "q11_sus_uso_frecuente",
        "Creo que me gustaría usar este medio con frecuencia.\n¿Prefieres este método de encuesta?",
    ),
    likert("q12_sus_complejo", "Encontré este medio innecesariamente complejo."),
    likert("q13_sus_facil", "Pensé que este medio era fácil de usar."),
    likert(
        "q14_sus_ayuda_tecnica",
        "Creo que necesitaría ayuda de una persona técnica para usar este medio.",
    ),
    likert(
        "q15_sus_integradas",
        "Encontré que las funciones de este medio estaban bien integradas.",
    ),
    likert("q16_sus_inconsistencia", "Pensé que había demasiada inconsistencia en este medio."),
    likert(
        "q17_sus_aprendizaje_rapido",
        "Imagino que la mayoría de las personas aprenderían a usar este medio muy rápido.",
    ),
    likert("q18_sus_incomodo", "Encontré este medio muy incómodo de usar."),
    likert("q19_sus_seguro", "Me sentí muy seguro/a usando este medio."),
    likert(
        "q20_sus_aprender_mucho",
        "Necesité aprender muchas cosas antes de poder usar este medio.",
    ),
]

SUS_COLUMNS = [
    question["column"] for question in QUESTIONS[SUS_FIRST_POSITION:SUS_LAST_POSITION]
]