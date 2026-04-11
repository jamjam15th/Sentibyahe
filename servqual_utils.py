# servqual_utils.py
# Central config for the SERVQUAL framework (land public transportation context).

SERVQUAL_DIMENSIONS = {
    "Tangibles": {
        "key": "tangibles", "icon": "🚌", "color_css": "tangibles", "hex": "#4a7c59",
        "desc": "Looks and condition of vehicles, stops/terminals, equipment, and staff presentation.",
    },
    "Reliability": {
        "key": "reliability", "icon": "🕐", "color_css": "reliability", "hex": "#1a5276",
        "desc": "Schedules, waiting times, trip predictability, and how reliably service holds up when conditions are tight.",
    },
    "Responsiveness": {
        "key": "responsiveness", "icon": "⚡", "color_css": "responsiveness", "hex": "#6c3483",
        "desc": "Speed of help, handling complaints, and how quickly the system or crew responds to passengers.",
    },
    "Assurance": {
        "key": "assurance", "icon": "🛡️", "color_css": "assurance", "hex": "#7d6608",
        "desc": "Competence and courtesy of drivers/operators, safety confidence, and trust in the service.",
    },
    "Empathy": {
        "key": "empathy", "icon": "🤝", "color_css": "empathy", "hex": "#922b21",
        "desc": "Understanding respondent needs, fairness, and care shown to different kinds of passengers.",
    },
}

DIM_KEYS = list(SERVQUAL_DIMENSIONS.keys())