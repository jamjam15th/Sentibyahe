# servqual_utils.py
# Central config for the SERVQUAL framework used across the PUV sentiment system.

SERVQUAL_DIMENSIONS = {
    "Tangibles": {
        "key": "tangibles", "icon": "🚌", "color_css": "tangibles", "hex": "#4a7c59",
        "desc": "Physical appearance of the vehicle, equipment, and driver's uniform.",
    },
    "Reliability": {
        "key": "reliability", "icon": "🕐", "color_css": "reliability", "hex": "#1a5276",
        "desc": "Ability to perform the promised service dependably and accurately.",
    },
    "Responsiveness": {
        "key": "responsiveness", "icon": "⚡", "color_css": "responsiveness", "hex": "#6c3483",
        "desc": "Willingness to help passengers and provide prompt service.",
    },
    "Assurance": {
        "key": "assurance", "icon": "🛡️", "color_css": "assurance", "hex": "#7d6608",
        "desc": "Knowledge, courtesy of the driver, and ability to inspire trust and safety.",
    },
    "Empathy": {
        "key": "empathy", "icon": "🤝", "color_css": "empathy", "hex": "#922b21",
        "desc": "Caring, individualized attention given to passengers.",
    },
}

DIM_KEYS = list(SERVQUAL_DIMENSIONS.keys())