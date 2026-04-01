"""Test unitari per app/core/presentation_model.py — TASK-P2 / TASK-02.

Verifica che to_dict() produca esattamente il JSON atteso dall'API Huidu,
confrontandolo con gli esempi in docs/PRESENTATION_FORMAT.md.
"""

from __future__ import annotations

import pytest

from app.core.presentation_model import (
    Area,
    DigitalClockItem,
    Effect,
    Font,
    ImageItem,
    Presentation,
    TextItem,
    VideoItem,
    item_from_dict,
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


# ---------------------------------------------------------------------------
# Test ImageItem — TASK-02
# ---------------------------------------------------------------------------


class TestImageItem:
    def test_tipo_impostato_automaticamente(self) -> None:
        item = ImageItem(file="img.png", fileMd5="abc", fileSize=1024)
        assert item.type == "image"

    def test_to_dict_chiavi(self) -> None:
        item = ImageItem(file="img.png", fileMd5="abc", fileSize=1024)
        d = item.to_dict()
        assert set(d.keys()) == {"type", "file", "fileMd5", "fileSize", "fit", "effect"}
        assert d["type"] == "image"
        assert d["fit"] == "stretch"

    def test_fit_values(self) -> None:
        for fit in ["fill", "center", "stretch", "tile"]:
            item = ImageItem(file="img.png", fileMd5="abc", fileSize=100, fit=fit)
            assert item.to_dict()["fit"] == fit

    def test_roundtrip_to_from_dict(self) -> None:
        original = ImageItem(
            file="http://example.com/img.png",
            fileMd5="abc123",
            fileSize=2048,
            fit="center",
            effect=Effect(type=17, speed=3, hold=1000),
        )
        rebuilt = ImageItem.from_dict(original.to_dict())
        assert rebuilt.file == original.file
        assert rebuilt.fileMd5 == original.fileMd5
        assert rebuilt.fileSize == original.fileSize
        assert rebuilt.fit == original.fit
        assert rebuilt.effect.type == original.effect.type


# ---------------------------------------------------------------------------
# Test VideoItem — TASK-02
# ---------------------------------------------------------------------------


class TestVideoItem:
    def test_tipo_impostato_automaticamente(self) -> None:
        item = VideoItem(file="vid.mp4", fileMd5="def", fileSize=10000)
        assert item.type == "video"

    def test_to_dict_chiavi(self) -> None:
        item = VideoItem(file="vid.mp4", fileMd5="def", fileSize=10000)
        d = item.to_dict()
        assert set(d.keys()) == {"type", "file", "fileMd5", "fileSize", "aspectRatio", "effect"}

    def test_aspect_ratio_default_false(self) -> None:
        item = VideoItem(file="vid.mp4", fileMd5="def", fileSize=10000)
        assert item.aspectRatio is False

    def test_roundtrip_to_from_dict(self) -> None:
        original = VideoItem(
            file="http://example.com/vid.mp4",
            fileMd5="xyz789",
            fileSize=50000,
            aspectRatio=True,
            effect=Effect(type=0, speed=5, hold=3000),
        )
        rebuilt = VideoItem.from_dict(original.to_dict())
        assert rebuilt.file == original.file
        assert rebuilt.aspectRatio is True
        assert rebuilt.effect.hold == 3000


# ---------------------------------------------------------------------------
# Test DigitalClockItem — TASK-02
# ---------------------------------------------------------------------------


class TestDigitalClockItem:
    def test_tipo_impostato_automaticamente(self) -> None:
        item = DigitalClockItem()
        assert item.type == "digitalClock"

    def test_to_dict_chiavi(self) -> None:
        d = DigitalClockItem().to_dict()
        assert set(d.keys()) == {"type", "timezone", "multiLine", "date", "time", "week"}

    def test_valori_default(self) -> None:
        item = DigitalClockItem()
        assert item.timezone == "+1:00"
        assert item.multiLine is True
        assert item.date["display"] == "true"

    def test_roundtrip_to_from_dict(self) -> None:
        original = DigitalClockItem(
            timezone="+2:00",
            multiLine=False,
            date={"format": 1, "color": "#ff0000", "display": "true"},
        )
        rebuilt = DigitalClockItem.from_dict(original.to_dict())
        assert rebuilt.timezone == "+2:00"
        assert rebuilt.multiLine is False
        assert rebuilt.date["color"] == "#ff0000"


# ---------------------------------------------------------------------------
# Test item_from_dict dispatcher — TASK-02
# ---------------------------------------------------------------------------


class TestItemFromDict:
    def test_dispatch_text(self) -> None:
        item = item_from_dict({"type": "text", "string": "hello"})
        assert isinstance(item, TextItem)
        assert item.string == "hello"

    def test_dispatch_image(self) -> None:
        item = item_from_dict({"type": "image", "file": "img.png", "fileMd5": "", "fileSize": 0})
        assert isinstance(item, ImageItem)

    def test_dispatch_video(self) -> None:
        item = item_from_dict({"type": "video", "file": "vid.mp4", "fileMd5": "", "fileSize": 0})
        assert isinstance(item, VideoItem)

    def test_dispatch_digital_clock(self) -> None:
        item = item_from_dict({"type": "digitalClock"})
        assert isinstance(item, DigitalClockItem)

    def test_tipo_sconosciuto_solleva(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="sconosciuto"):
            item_from_dict({"type": "unknown"})

    def test_tipo_mancante_solleva(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="sconosciuto"):
            item_from_dict({})


# ---------------------------------------------------------------------------
# Test from_dict roundtrip completi — TASK-02
# ---------------------------------------------------------------------------


class TestFromDictRoundtrip:
    def test_effect_roundtrip(self) -> None:
        e = Effect(type=17, speed=2, hold=999)
        assert Effect.from_dict(e.to_dict()).type == 17

    def test_font_roundtrip(self) -> None:
        f = Font(name="Courier", size=20, bold=True, color="#00ff00")
        rebuilt = Font.from_dict(f.to_dict())
        assert rebuilt.name == "Courier"
        assert rebuilt.bold is True

    def test_text_item_roundtrip(self) -> None:
        t = TextItem(string="Ciao", alignment="left", PlayText=True)
        rebuilt = TextItem.from_dict(t.to_dict())
        assert rebuilt.string == "Ciao"
        assert rebuilt.alignment == "left"
        assert rebuilt.PlayText is True

    def test_area_roundtrip(self) -> None:
        a = Area(x=10, y=20, width=100, height=50, item=[TextItem(string="X")])
        rebuilt = Area.from_dict(a.to_dict())
        assert rebuilt.x == 10
        assert rebuilt.width == 100
        assert len(rebuilt.item) == 1
        assert isinstance(rebuilt.item[0], TextItem)

    def test_area_con_image_item(self) -> None:
        a = Area(
            x=0, y=0, width=128, height=64,
            item=[ImageItem(file="img.png", fileMd5="abc", fileSize=1024)],
        )
        rebuilt = Area.from_dict(a.to_dict())
        assert isinstance(rebuilt.item[0], ImageItem)

    def test_presentation_roundtrip(self) -> None:
        p = Presentation.simple_text("Demo", "Hello")
        d = p.to_dict()
        rebuilt = Presentation.from_dict(d)
        assert rebuilt.name == "Demo"
        assert rebuilt.uuid == p.uuid
        assert len(rebuilt.area) == 1
        assert isinstance(rebuilt.area[0].item[0], TextItem)

    def test_presentation_con_play_control(self) -> None:
        p = Presentation(
            name="Pianificata",
            area=[Area(x=0, y=0, width=128, height=64, item=[TextItem(string="Y")])],
            play_control={"duration": "00:00:30"},
        )
        rebuilt = Presentation.from_dict(p.to_dict())
        assert rebuilt.play_control == {"duration": "00:00:30"}


# ---------------------------------------------------------------------------
# Test Presentation.simple_image — TASK-02
# ---------------------------------------------------------------------------


class TestSimpleImage:
    def test_crea_presentazione_immagine(self) -> None:
        p = Presentation.simple_image(
            "Test Img", "http://img.png", "abc", 1024,
            screen_width=256, screen_height=128,
        )
        assert len(p.area) == 1
        assert isinstance(p.area[0].item[0], ImageItem)

    def test_dimensioni_area(self) -> None:
        p = Presentation.simple_image(
            "Test", "url", "md5", 500,
            screen_width=200, screen_height=100,
        )
        assert p.area[0].width == 200
        assert p.area[0].height == 100

    def test_to_dict_valido(self) -> None:
        p = Presentation.simple_image("V", "url", "md5", 500)
        d = p.to_dict()
        assert d["area"][0]["item"][0]["type"] == "image"
