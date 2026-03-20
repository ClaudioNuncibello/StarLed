"""Test unitari per app/api/auth_signer.py — TASK-01.

Tutti i test usano valori di firma calcolati in modo deterministico
(input noti → output atteso verificato manualmente).
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from app.api.auth_signer import AuthSigner, _hmac_md5, _http_date


# ---------------------------------------------------------------------------
# Costanti per test deterministici
# ---------------------------------------------------------------------------

SDK_KEY = "testSdkKey12345"
SDK_SECRET = "testSdkSecret999"
FIXED_DATE = "Wed, 09 Aug 2023 07:27:44 GMT"
FIXED_BODY = '{"method":"getAll","data":[]}'
FIXED_UUID = "00000000-0000-0000-0000-000000000001"


def _expected_sign(message: str) -> str:
    """Calcola HMAC-MD5 atteso — replica indipendente per confronto."""
    return hmac.new(
        SDK_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.md5,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Test _http_date
# ---------------------------------------------------------------------------


class TestHttpDate:
    """Verifica la formattazione della data RFC 7231."""

    def test_formato_corretto(self) -> None:
        """La data deve seguire il formato RFC 7231."""
        from datetime import datetime, timezone

        dt = datetime(2023, 8, 9, 7, 27, 44, tzinfo=timezone.utc)
        result = _http_date(dt)
        assert result == "Wed, 09 Aug 2023 07:27:44 GMT"

    def test_padding_giorno(self) -> None:
        """I giorni a singola cifra devono avere zero padding."""
        from datetime import datetime, timezone

        dt = datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc)
        result = _http_date(dt)
        assert result.startswith("Fri, 05 Jan 2024")

    def test_senza_argomenti_non_solleva(self) -> None:
        """Chiamata senza argomenti deve restituire una stringa non vuota."""
        result = _http_date()
        assert isinstance(result, str)
        assert len(result) > 0
        assert result.endswith("GMT")

    def test_nomi_mesi_inglesi(self) -> None:
        """I nomi dei mesi devono essere in inglese (non dipendere dal locale)."""
        from datetime import datetime, timezone

        mesi_attesi = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        for mese_idx, nome in enumerate(mesi_attesi, start=1):
            dt = datetime(2024, mese_idx, 15, 12, 0, 0, tzinfo=timezone.utc)
            result = _http_date(dt)
            assert nome in result, f"Mese {mese_idx}: atteso '{nome}' in '{result}'"

    def test_nomi_giorni_inglesi(self) -> None:
        """I nomi dei giorni devono essere in inglese."""
        from datetime import datetime, timezone

        # 2024-01-01 = lunedì
        giorni_attesi = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for offset, nome in enumerate(giorni_attesi):
            dt = datetime(2024, 1, 1 + offset, 12, 0, 0, tzinfo=timezone.utc)
            result = _http_date(dt)
            assert result.startswith(nome), f"Giorno {offset}: atteso '{nome}', ottenuto '{result}'"


# ---------------------------------------------------------------------------
# Test _hmac_md5
# ---------------------------------------------------------------------------


class TestHmacMd5:
    """Verifica il calcolo HMAC-MD5."""

    def test_deterministico(self) -> None:
        """Stesso input → stessa firma."""
        sign1 = _hmac_md5("messaggio", "segreto")
        sign2 = _hmac_md5("messaggio", "segreto")
        assert sign1 == sign2

    def test_valore_noto(self) -> None:
        """Verifica con valore calcolato indipendentemente."""
        atteso = hmac.new(
            b"chiavesegreta",
            b"payload",
            hashlib.md5,
        ).hexdigest()
        assert _hmac_md5("payload", "chiavesegreta") == atteso

    def test_lowercase_hex(self) -> None:
        """Il digest deve essere esadecimale minuscolo."""
        result = _hmac_md5("abc", "xyz")
        assert result == result.lower()
        assert len(result) == 32
        assert all(c in "0123456789abcdef" for c in result)

    def test_sensibile_al_messaggio(self) -> None:
        """Messaggi diversi devono produrre firme diverse."""
        sign_a = _hmac_md5("messaggio_A", SDK_SECRET)
        sign_b = _hmac_md5("messaggio_B", SDK_SECRET)
        assert sign_a != sign_b

    def test_sensibile_al_segreto(self) -> None:
        """Segreti diversi devono produrre firme diverse."""
        sign_a = _hmac_md5("stesso_messaggio", "segreto_A")
        sign_b = _hmac_md5("stesso_messaggio", "segreto_B")
        assert sign_a != sign_b


# ---------------------------------------------------------------------------
# Test AuthSigner.__init__
# ---------------------------------------------------------------------------


class TestAuthSignerInit:
    """Verifica la costruzione di AuthSigner."""

    def test_costruzione_valida(self) -> None:
        """Deve costruirsi senza eccezioni con credenziali valide."""
        signer = AuthSigner(sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)
        assert signer is not None

    def test_sdk_key_vuoto_solleva(self) -> None:
        """sdk_key vuoto deve sollevare ValueError."""
        with pytest.raises(ValueError, match="sdk_key"):
            AuthSigner(sdk_key="", sdk_secret=SDK_SECRET)

    def test_sdk_secret_vuoto_solleva(self) -> None:
        """sdk_secret vuoto deve sollevare ValueError."""
        with pytest.raises(ValueError, match="sdk_secret"):
            AuthSigner(sdk_key=SDK_KEY, sdk_secret="")


# ---------------------------------------------------------------------------
# Test AuthSigner.sign_request — regola generale
# ---------------------------------------------------------------------------


class TestSignRequest:
    """Verifica sign_request() con la regola generale."""

    @pytest.fixture
    def signer(self) -> AuthSigner:
        return AuthSigner(sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)

    def test_chiavi_header_presenti(self, signer: AuthSigner) -> None:
        """Gli header devono contenere tutte le chiavi richieste."""
        headers = signer.sign_request(
            body=FIXED_BODY, date=FIXED_DATE, request_id=FIXED_UUID
        )
        for chiave in ("sdkKey", "date", "sign", "requestId", "Content-Type"):
            assert chiave in headers, f"Chiave mancante: {chiave}"

    def test_sdk_key_corretto(self, signer: AuthSigner) -> None:
        """L'header sdkKey deve corrispondere all'SDK Key fornito."""
        headers = signer.sign_request(date=FIXED_DATE)
        assert headers["sdkKey"] == SDK_KEY

    def test_date_propagato(self, signer: AuthSigner) -> None:
        """La data passata deve essere riportata nell'header."""
        headers = signer.sign_request(date=FIXED_DATE)
        assert headers["date"] == FIXED_DATE

    def test_content_type_json(self, signer: AuthSigner) -> None:
        """Content-Type deve essere application/json."""
        headers = signer.sign_request(date=FIXED_DATE)
        assert headers["Content-Type"] == "application/json"

    def test_firma_regola_generale_con_body(self, signer: AuthSigner) -> None:
        """sign = HMAC-MD5(body + sdkKey + date, sdkSecret)."""
        headers = signer.sign_request(
            body=FIXED_BODY, date=FIXED_DATE, request_id=FIXED_UUID
        )
        messaggio = FIXED_BODY + SDK_KEY + FIXED_DATE
        attesa = _expected_sign(messaggio)
        assert headers["sign"] == attesa

    def test_firma_body_vuoto(self, signer: AuthSigner) -> None:
        """Body vuoto (GET): sign = HMAC-MD5('' + sdkKey + date, sdkSecret)."""
        headers = signer.sign_request(body="", date=FIXED_DATE)
        messaggio = "" + SDK_KEY + FIXED_DATE
        attesa = _expected_sign(messaggio)
        assert headers["sign"] == attesa

    def test_firma_varia_con_body(self, signer: AuthSigner) -> None:
        """Body diverso → firma diversa."""
        h1 = signer.sign_request(body='{"method":"getAll"}', date=FIXED_DATE)
        h2 = signer.sign_request(body='{"method":"replace"}', date=FIXED_DATE)
        assert h1["sign"] != h2["sign"]

    def test_firma_varia_con_data(self, signer: AuthSigner) -> None:
        """Data diversa → firma diversa."""
        h1 = signer.sign_request(date="Mon, 01 Jan 2024 00:00:00 GMT")
        h2 = signer.sign_request(date="Tue, 02 Jan 2024 00:00:00 GMT")
        assert h1["sign"] != h2["sign"]

    def test_request_id_fornito(self, signer: AuthSigner) -> None:
        """UUID fornito esplicitamente deve essere usato."""
        headers = signer.sign_request(date=FIXED_DATE, request_id=FIXED_UUID)
        assert headers["requestId"] == FIXED_UUID

    def test_request_id_autogenerato(self, signer: AuthSigner) -> None:
        """UUID autogenerato deve essere una stringa non vuota."""
        headers = signer.sign_request(date=FIXED_DATE)
        assert isinstance(headers["requestId"], str)
        assert len(headers["requestId"]) > 0

    def test_request_id_diverso_ogni_chiamata(self, signer: AuthSigner) -> None:
        """Due chiamate senza request_id devono avere UUID diversi."""
        h1 = signer.sign_request(date=FIXED_DATE)
        h2 = signer.sign_request(date=FIXED_DATE)
        assert h1["requestId"] != h2["requestId"]


# ---------------------------------------------------------------------------
# Test AuthSigner.sign_file_upload — regola file
# ---------------------------------------------------------------------------


class TestSignFileUpload:
    """Verifica sign_file_upload() con la regola upload file."""

    @pytest.fixture
    def signer(self) -> AuthSigner:
        return AuthSigner(sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)

    def test_chiavi_header_presenti(self, signer: AuthSigner) -> None:
        """Gli header devono contenere sdkKey, date, sign, requestId."""
        headers = signer.sign_file_upload(date=FIXED_DATE)
        for chiave in ("sdkKey", "date", "sign", "requestId"):
            assert chiave in headers, f"Chiave mancante: {chiave}"

    def test_no_content_type(self, signer: AuthSigner) -> None:
        """Content-Type NON deve essere presente (gestito da requests per multipart)."""
        headers = signer.sign_file_upload(date=FIXED_DATE)
        assert "Content-Type" not in headers

    def test_firma_regola_file(self, signer: AuthSigner) -> None:
        """sign = HMAC-MD5(sdkKey + date, sdkSecret)."""
        headers = signer.sign_file_upload(date=FIXED_DATE)
        messaggio = SDK_KEY + FIXED_DATE
        attesa = _expected_sign(messaggio)
        assert headers["sign"] == attesa

    def test_firma_file_diversa_da_generale(self, signer: AuthSigner) -> None:
        """La firma regola file deve differire dalla regola generale (body='')."""
        h_file = signer.sign_file_upload(date=FIXED_DATE)
        h_gen = signer.sign_request(body="", date=FIXED_DATE)
        # regola generale: body('') + sdkKey + date → sdkKey + date (coincide!)
        # Quindi body == '' → le firme saranno uguali: verifichiamo questo caso
        # La differenza vera si vede con body non vuoto
        h_gen_body = signer.sign_request(body=FIXED_BODY, date=FIXED_DATE)
        assert h_file["sign"] != h_gen_body["sign"]

    def test_sdk_key_propagato(self, signer: AuthSigner) -> None:
        """sdkKey deve corrispondere a quello fornito."""
        headers = signer.sign_file_upload(date=FIXED_DATE)
        assert headers["sdkKey"] == SDK_KEY


# ---------------------------------------------------------------------------
# Test AuthSigner.sign_url — regola URL (firma come query string)
# ---------------------------------------------------------------------------


class TestSignUrl:
    """Verifica sign_url() — firma Huidu come parametri query string."""

    BASE_URL = "http://127.0.0.1:30080/api/file/immagine.png"

    @pytest.fixture
    def signer(self) -> AuthSigner:
        return AuthSigner(sdk_key=SDK_KEY, sdk_secret=SDK_SECRET)

    def test_url_contiene_sdk_key(self, signer: AuthSigner) -> None:
        """L'URL firmato deve contenere sdkKey."""
        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert f"sdkKey={SDK_KEY}" in result

    def test_url_contiene_sign(self, signer: AuthSigner) -> None:
        """L'URL firmato deve contenere il parametro sign."""
        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert "sign=" in result

    def test_url_contiene_date(self, signer: AuthSigner) -> None:
        """L'URL firmato deve contenere il parametro date URL-encoded."""
        from urllib.parse import quote

        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert f"date={quote(FIXED_DATE)}" in result

    def test_firma_corretta(self, signer: AuthSigner) -> None:
        """La firma nell'URL deve essere HMAC-MD5(sdkKey + date, sdkSecret)."""
        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        attesa = _expected_sign(SDK_KEY + FIXED_DATE)
        assert f"sign={attesa}" in result

    def test_url_senza_punto_interrogativo(self, signer: AuthSigner) -> None:
        """URL senza ? esistente → aggiunge ? prima dei parametri."""
        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert result.startswith(self.BASE_URL + "?")

    def test_url_con_punto_interrogativo(self, signer: AuthSigner) -> None:
        """URL con ? già presente → aggiunge & prima dei parametri."""
        base = self.BASE_URL + "?token=abc"
        result = signer.sign_url(base, date=FIXED_DATE)
        assert "?token=abc&" in result

    def test_url_inizia_con_base(self, signer: AuthSigner) -> None:
        """L'URL firmato deve iniziare con l'URL originale."""
        result = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert result.startswith(self.BASE_URL)

    def test_firma_uguale_a_sign_file_upload(self, signer: AuthSigner) -> None:
        """La firma di sign_url deve essere identica a quella di sign_file_upload."""
        h_file = signer.sign_file_upload(date=FIXED_DATE)
        signed = signer.sign_url(self.BASE_URL, date=FIXED_DATE)
        assert f"sign={h_file['sign']}" in signed
