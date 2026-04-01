"""Test unitari per app/core/json_builder.py — TASK-06.

Verifica build_payload() e la validazione strutturale.
"""

from __future__ import annotations

import pytest

from app.core.json_builder import build_payload
from app.core.presentation_model import Area, Presentation, TextItem


# ---------------------------------------------------------------------------
# Fixture comuni
# ---------------------------------------------------------------------------

DEVICE_ID = "C16-D00-A000F"


@pytest.fixture
def simple_presentation() -> Presentation:
    return Presentation.simple_text("Demo", "Hello LED")


# ---------------------------------------------------------------------------
# Test build_payload
# ---------------------------------------------------------------------------


class TestBuildPayload:
    def test_method_replace(self, simple_presentation: Presentation) -> None:
        payload = build_payload([simple_presentation], "replace", DEVICE_ID)
        assert payload["method"] == "replace"
        assert payload["id"] == DEVICE_ID
        assert len(payload["data"]) == 1

    def test_method_append(self, simple_presentation: Presentation) -> None:
        payload = build_payload([simple_presentation], "append", DEVICE_ID)
        assert payload["method"] == "append"

    def test_presentazioni_multiple(self) -> None:
        p1 = Presentation.simple_text("P1", "Text1")
        p2 = Presentation.simple_text("P2", "Text2")
        payload = build_payload([p1, p2], "replace", DEVICE_ID)
        assert len(payload["data"]) == 2
        assert payload["data"][0]["name"] == "P1"
        assert payload["data"][1]["name"] == "P2"

    def test_payload_struttura_corretta(self, simple_presentation: Presentation) -> None:
        payload = build_payload([simple_presentation], "replace", DEVICE_ID)
        assert set(payload.keys()) == {"method", "id", "data"}

    def test_data_contiene_area(self, simple_presentation: Presentation) -> None:
        payload = build_payload([simple_presentation], "replace", DEVICE_ID)
        pres_data = payload["data"][0]
        assert "area" in pres_data
        assert len(pres_data["area"]) == 1


# ---------------------------------------------------------------------------
# Test validazione
# ---------------------------------------------------------------------------


class TestBuildPayloadValidazione:
    def test_lista_vuota_solleva(self) -> None:
        with pytest.raises(ValueError, match="presentazione"):
            build_payload([], "replace", DEVICE_ID)

    def test_device_id_vuoto_solleva(self, simple_presentation: Presentation) -> None:
        with pytest.raises(ValueError, match="device_id"):
            build_payload([simple_presentation], "replace", "")

    def test_area_vuota_solleva(self) -> None:
        pres = Presentation(name="Vuota", area=[])
        with pytest.raises(ValueError, match="area"):
            build_payload([pres], "replace", DEVICE_ID)

    def test_item_vuoto_solleva(self) -> None:
        pres = Presentation(
            name="NoItem",
            area=[Area(x=0, y=0, width=128, height=64, item=[])],
        )
        with pytest.raises(ValueError, match="item"):
            build_payload([pres], "replace", DEVICE_ID)

    def test_coordinate_negative_solleva(self) -> None:
        pres = Presentation(
            name="NegX",
            area=[Area(x=-1, y=0, width=128, height=64, item=[TextItem(string="X")])],
        )
        with pytest.raises(ValueError, match="negative"):
            build_payload([pres], "replace", DEVICE_ID)

    def test_dimensioni_zero_solleva(self) -> None:
        pres = Presentation(
            name="ZeroW",
            area=[Area(x=0, y=0, width=0, height=64, item=[TextItem(string="X")])],
        )
        with pytest.raises(ValueError, match="positive"):
            build_payload([pres], "replace", DEVICE_ID)

    def test_uuid_vuoto_solleva(self) -> None:
        pres = Presentation(
            name="NoUUID",
            area=[Area(x=0, y=0, width=128, height=64, uuid="", item=[TextItem(string="X")])],
        )
        with pytest.raises(ValueError, match="UUID"):
            build_payload([pres], "replace", DEVICE_ID)
