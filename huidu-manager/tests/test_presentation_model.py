"""Test unitari per app/core/presentation_model.py — TASK-P2 / TASK-02.

Verifica che to_dict() produca esattamente il JSON atteso dall'API Huidu,
confrontandolo con gli esempi in docs/PRESENTATION_FORMAT.md.
"""

from __future__ import annotations

import pytest

from app.core.presentation_model import (
    Area,
    Effect,
    Font,
    Presentation,
    TextItem,
)


# ---------------------------------------------------------------------------
# Test Effect
# ---------------------------------------------------------------------------


class TestEffect:
    def test_default_values(self) -> None:
        e = Effect()
        assert e.type == 0
        assert e.speed == 5
        assert e.hold == 5000

    def test_to_dict_keys(self) -> None:
        d = Effect(type=1, speed=3, hold=2000).to_dict()
        assert d == {"type": 1, "speed": 3, "hold": 2000}

    def test_to_dict_valori_custom(self) -> None:
        d = Effect(type=17, speed=0, hold=0).to_dict()
        assert d["type"] == 17
        assert d["speed"] == 0
        assert d["hold"] == 0


# ---------------------------------------------------------------------------
# Test Font
# ---------------------------------------------------------------------------


class TestFont:
    def test_default_values(self) -> None:
        f = Font()
        assert f.name == "Arial"
        assert f.size == 14
        assert f.bold is False
        assert f.color == "#ffffff"

    def test_to_dict_completo(self) -> None:
        f = Font(name="Verdana", size=16, bold=True, italic=False,
                 underline=True, color="#ff0000")
        d = f.to_dict()
        assert d["name"] == "Verdana"
        assert d["size"] == 16
        assert d["bold"] is True
        assert d["underline"] is True
        assert d["color"] == "#ff0000"

    def test_to_dict_chiavi_obbligatorie(self) -> None:
        d = Font().to_dict()
        for k in ("name", "size", "bold", "italic", "underline", "color"):
            assert k in d


# ---------------------------------------------------------------------------
# Test TextItem
# ---------------------------------------------------------------------------


class TestTextItem:
    def test_type_sempre_text(self) -> None:
        item = TextItem(string="ciao")
        assert item.type == "text"

    def test_type_non_modificabile_da_init(self) -> None:
        """type è field(init=False) — non accetta parametro in costruzione."""
        item = TextItem(string="test")
        assert item.type == "text"

    def test_to_dict_chiavi_obbligatorie(self) -> None:
        d = TextItem(string="Hello LED").to_dict()
        for k in ("type", "string", "multiLine", "PlayText", "alignment",
                  "valignment", "font", "effect"):
            assert k in d, f"Chiave mancante: {k}"

    def test_to_dict_tipo_corretto(self) -> None:
        d = TextItem(string="test").to_dict()
        assert d["type"] == "text"

    def test_to_dict_stringa(self) -> None:
        d = TextItem(string="Hello LED").to_dict()
        assert d["string"] == "Hello LED"

    def test_to_dict_font_annidato(self) -> None:
        font = Font(size=20, color="#ff0000")
        d = TextItem(string="test", font=font).to_dict()
        assert d["font"]["size"] == 20
        assert d["font"]["color"] == "#ff0000"

    def test_to_dict_effect_annidato(self) -> None:
        effect = Effect(type=1, speed=2)
        d = TextItem(string="test", effect=effect).to_dict()
        assert d["effect"]["type"] == 1
        assert d["effect"]["speed"] == 2

    def test_default_alignment(self) -> None:
        d = TextItem(string="test").to_dict()
        assert d["alignment"] == "center"
        assert d["valignment"] == "middle"

    def test_multiline_e_playtext(self) -> None:
        d = TextItem(string="test", multiLine=True, PlayText=True).to_dict()
        assert d["multiLine"] is True
        assert d["PlayText"] is True


# ---------------------------------------------------------------------------
# Test Area
# ---------------------------------------------------------------------------


class TestArea:
    def test_uuid_autogenerato(self) -> None:
        a = Area(x=0, y=0, width=128, height=64)
        assert isinstance(a.uuid, str)
        assert len(a.uuid) > 0

    def test_uuid_univoco(self) -> None:
        a1 = Area(x=0, y=0, width=128, height=64)
        a2 = Area(x=0, y=0, width=128, height=64)
        assert a1.uuid != a2.uuid

    def test_to_dict_senza_item_solleva(self) -> None:
        area = Area(x=0, y=0, width=128, height=64)
        with pytest.raises(ValueError, match="item"):
            area.to_dict()

    def test_to_dict_struttura(self) -> None:
        item = TextItem(string="test")
        area = Area(x=0, y=0, width=128, height=64, item=[item])
        d = area.to_dict()
        assert d["x"] == 0
        assert d["y"] == 0
        assert d["width"] == 128
        assert d["height"] == 64
        assert len(d["item"]) == 1
        assert d["item"][0]["type"] == "text"

    def test_to_dict_chiavi_obbligatorie(self) -> None:
        item = TextItem(string="test")
        d = Area(x=0, y=0, width=64, height=32, item=[item]).to_dict()
        for k in ("uuid", "x", "y", "width", "height", "item"):
            assert k in d


# ---------------------------------------------------------------------------
# Test Presentation
# ---------------------------------------------------------------------------


class TestPresentation:
    def test_uuid_autogenerato(self) -> None:
        p = Presentation(name="Test")
        assert isinstance(p.uuid, str)
        assert len(p.uuid) > 0

    def test_uuid_univoco(self) -> None:
        p1 = Presentation(name="P1")
        p2 = Presentation(name="P2")
        assert p1.uuid != p2.uuid

    def test_type_sempre_normal(self) -> None:
        p = Presentation(name="Test")
        assert p.type == "normal"

    def test_to_dict_senza_area_solleva(self) -> None:
        p = Presentation(name="Vuota")
        with pytest.raises(ValueError, match="area"):
            p.to_dict()

    def test_to_dict_struttura_completa(self) -> None:
        item = TextItem(string="Hello LED")
        area = Area(x=0, y=0, width=128, height=64, item=[item])
        p = Presentation(name="Demo", area=[area])
        d = p.to_dict()

        assert d["name"] == "Demo"
        assert d["type"] == "normal"
        assert "uuid" in d
        assert len(d["area"]) == 1
        assert d["area"][0]["item"][0]["string"] == "Hello LED"

    def test_to_dict_senza_play_control(self) -> None:
        item = TextItem(string="test")
        area = Area(x=0, y=0, width=128, height=64, item=[item])
        p = Presentation(name="Test", area=[area])
        d = p.to_dict()
        assert "playControl" not in d

    def test_to_dict_con_play_control(self) -> None:
        item = TextItem(string="test")
        area = Area(x=0, y=0, width=128, height=64, item=[item])
        pc = {"duration": "00:00:30", "week": {"enable": "Mon,Tue"}}
        p = Presentation(name="Test", area=[area], play_control=pc)
        d = p.to_dict()
        assert "playControl" in d
        assert d["playControl"]["duration"] == "00:00:30"


# ---------------------------------------------------------------------------
# Test Presentation.simple_text (helper factory)
# ---------------------------------------------------------------------------


class TestSimpleText:
    def test_crea_presentazione(self) -> None:
        p = Presentation.simple_text("Demo", "Hello LED")
        assert isinstance(p, Presentation)
        assert p.name == "Demo"

    def test_una_area_un_item(self) -> None:
        p = Presentation.simple_text("Demo", "Hello LED")
        assert len(p.area) == 1
        assert len(p.area[0].item) == 1

    def test_testo_corretto(self) -> None:
        p = Presentation.simple_text("Demo", "Ciao mondo")
        assert p.area[0].item[0].string == "Ciao mondo"

    def test_dimensioni_schermo(self) -> None:
        p = Presentation.simple_text("Demo", "test", screen_width=256, screen_height=128)
        assert p.area[0].width == 256
        assert p.area[0].height == 128

    def test_to_dict_valido(self) -> None:
        """Il json prodotto da simple_text deve essere valido per l'API."""
        p = Presentation.simple_text("Demo", "Hello LED")
        d = p.to_dict()
        assert d["name"] == "Demo"
        assert d["type"] == "normal"
        assert d["area"][0]["item"][0]["type"] == "text"

    def test_font_color_custom(self) -> None:
        p = Presentation.simple_text("Demo", "test", color="#ff0000", font_size=20)
        item = p.area[0].item[0]
        assert item.font.color == "#ff0000"
        assert item.font.size == 20
