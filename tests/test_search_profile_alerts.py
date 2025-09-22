from datetime import datetime

from gui.models.search_profile import SearchProfile


def test_should_trigger_alert_requires_tracking_and_low_success():
    profile = SearchProfile("Perfil Test", ["criterio"], alert_recipient="alert@example.com")

    # Sin seguimiento activo no debe alertar
    assert not profile.should_trigger_alert()

    profile.track_optimal = True
    profile.optimal_executions = 100
    profile.update_search_results(80)

    assert profile.should_trigger_alert()

    # Después de registrar la alerta no debe repetirse sin una nueva búsqueda
    profile.record_alert_sent()
    assert not profile.should_trigger_alert()

    # Una nueva búsqueda con éxito alto evita la alerta
    profile.update_search_results(95)
    assert not profile.should_trigger_alert()

    # Reducir nuevamente el éxito debería activar alerta
    profile.update_search_results(50)
    assert profile.should_trigger_alert()

    # Quitar destinatario impide el envío
    profile.alert_recipient = ""
    assert not profile.should_trigger_alert()


def test_alert_fields_are_serialized_and_restored():
    profile = SearchProfile("Perfil Serializado", ["criterio"], alert_recipient="alert@example.com")
    profile.track_optimal = True
    profile.optimal_executions = 50
    profile.update_search_results(10)
    profile.record_alert_sent()

    data = profile.to_dict()

    assert data["alert_recipient"] == "alert@example.com"
    assert data["last_alert_sent"] is not None

    restored = SearchProfile.from_dict(data)

    assert restored.alert_recipient == "alert@example.com"
    assert isinstance(restored.last_alert_sent, datetime)
    assert restored.last_alert_sent is not None
