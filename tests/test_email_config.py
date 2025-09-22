"""Tests for the email recipient configuration helpers."""

from services.email_config import (
    DEFAULT_SUBJECT_TEMPLATES,
    FREQUENCIES,
    get_frequency_settings,
    normalize_recipients_config,
)


def test_normalize_returns_defaults_when_config_is_missing():
    config = normalize_recipients_config(None)

    for freq in FREQUENCIES:
        assert config[freq]["recipient"] == ""
        assert config[freq]["cc"] == ""
        assert config[freq]["subject_template"] == DEFAULT_SUBJECT_TEMPLATES[freq]


def test_normalize_supports_legacy_structure():
    raw_config = {
        "recipient": "  main@example.com  ",
        "cc": "cc1@example.com , cc2@example.com",
        "subject_template_daily": "Daily {date}",
    }

    config = normalize_recipients_config(raw_config)

    for freq in FREQUENCIES:
        assert config[freq]["recipient"] == "main@example.com"
        assert config[freq]["cc"] == "cc1@example.com , cc2@example.com"

    assert config["daily"]["subject_template"] == "Daily {date}"
    assert config["weekly"]["subject_template"] == DEFAULT_SUBJECT_TEMPLATES["weekly"]


def test_get_frequency_settings_uses_specific_values():
    raw_config = {
        "daily": {
            "recipient": "daily@example.com",
            "cc": "daily.cc@example.com",
            "subject_template": "Daily custom {date}",
        },
        "weekly": {
            "recipient": "weekly@example.com",
            "subject_template": "Weekly custom {date}",
        },
    }

    weekly_settings = get_frequency_settings(raw_config, "weekly")
    assert weekly_settings["recipient"] == "weekly@example.com"
    assert weekly_settings["cc"] == ""
    assert weekly_settings["subject_template"] == "Weekly custom {date}"

    fallback_settings = get_frequency_settings(raw_config, "unknown")
    assert fallback_settings["recipient"] == "daily@example.com"
    assert fallback_settings["subject_template"] == "Daily custom {date}"
