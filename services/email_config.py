"""Utilities to manage email recipient configuration for reports."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Optional

FREQUENCIES = ("daily", "weekly", "monthly")

FREQUENCY_LABELS = {
    "daily": "diario",
    "weekly": "semanal",
    "monthly": "mensual",
}

FREQUENCY_DISPLAY_NAMES = {
    freq: f"Reporte {FREQUENCY_LABELS[freq].capitalize()}"
    for freq in FREQUENCIES
}

DEFAULT_SUBJECT_TEMPLATES = {
    "daily": "Reporte Diario de Búsqueda de Correos - {date}",
    "weekly": "Reporte Semanal de Búsqueda de Correos - {date}",
    "monthly": "Reporte Mensual de Búsqueda de Correos - {date}",
}

DEFAULT_RECIPIENT_CONFIG: Dict[str, Dict[str, str]] = {
    freq: {
        "recipient": "",
        "cc": "",
        "subject_template": DEFAULT_SUBJECT_TEMPLATES[freq],
    }
    for freq in FREQUENCIES
}

LEGACY_SUBJECT_KEYS = {
    "daily": "subject_template_daily",
    "weekly": "subject_template_weekly",
    "monthly": "subject_template_monthly",
}


def _sanitize_text(value: Optional[str]) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def normalize_recipients_config(raw_config: Optional[Dict]) -> Dict[str, Dict[str, str]]:
    """Return a normalized recipient configuration.

    The function ensures that each supported frequency has a dictionary with
    the keys ``recipient``, ``cc`` and ``subject_template``. It also maintains
    backwards compatibility with the previous flat configuration format where a
    single recipient/cc and independent subject template keys were stored at the
    root level.
    """

    config = deepcopy(DEFAULT_RECIPIENT_CONFIG)

    if not isinstance(raw_config, dict):
        return config

    global_recipient = _sanitize_text(raw_config.get("recipient"))
    global_cc = _sanitize_text(raw_config.get("cc"))

    subject_fallbacks = {
        freq: _sanitize_text(raw_config.get(LEGACY_SUBJECT_KEYS[freq]))
        or DEFAULT_SUBJECT_TEMPLATES[freq]
        for freq in FREQUENCIES
    }

    for freq in FREQUENCIES:
        freq_config = raw_config.get(freq)
        if isinstance(freq_config, dict):
            recipient = _sanitize_text(freq_config.get("recipient", global_recipient))
            cc_value = _sanitize_text(freq_config.get("cc", global_cc))
            subject_template = _sanitize_text(freq_config.get("subject_template")) or subject_fallbacks[freq]
        else:
            recipient = global_recipient
            cc_value = global_cc
            subject_template = subject_fallbacks[freq]

        config[freq] = {
            "recipient": recipient,
            "cc": cc_value,
            "subject_template": subject_template or DEFAULT_SUBJECT_TEMPLATES[freq],
        }

    return config


def get_frequency_settings(
    config: Optional[Dict[str, Dict[str, str]]],
    frequency: str,
) -> Dict[str, str]:
    """Get configuration for a specific frequency with safe fallbacks."""

    if frequency not in FREQUENCIES:
        frequency = "daily"

    normalized = normalize_recipients_config(config)
    settings = normalized.get(frequency, {})

    recipient = _sanitize_text(settings.get("recipient"))
    cc_value = _sanitize_text(settings.get("cc"))
    subject_template = _sanitize_text(settings.get("subject_template")) or DEFAULT_SUBJECT_TEMPLATES[frequency]

    return {
        "recipient": recipient,
        "cc": cc_value,
        "subject_template": subject_template,
    }
