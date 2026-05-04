"""Discovery automatica dei gateway Huidu sulla subnet locale.

Scansiona la rete locale cercando host con la porta 30080 aperta
e verifica che rispondano come gateway Huidu validi.

NON importa da ``app/ui/`` — backend puro.

Example::

    gateways = discover_gateways(sdk_key="...", sdk_secret="...", timeout=0.5)
    for gw in gateways:
        print(f"Gateway {gw.host}: {gw.device_ids}")
"""

from __future__ import annotations

import ipaddress
import logging
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import requests

from app.api.auth_signer import AuthSigner

logger = logging.getLogger(__name__)

_HUIDU_PORT = 30080
# Timeout per ogni singola connessione TCP durante lo scan
_CONNECT_TIMEOUT = 0.5
# Timeout per la chiamata HTTP di verifica
_HTTP_VERIFY_TIMEOUT = 3
# Numero massimo di thread paralleli per lo scan
_MAX_WORKERS = 64


@dataclass
class DiscoveredGateway:
    """Gateway Huidu trovato sulla rete locale.

    Attributes:
        host: Indirizzo IP del gateway (es. ``"192.168.1.33"``).
        port: Porta del gateway (default ``30080``).
        device_ids: Lista degli ID controller connessi al gateway.
    """

    host: str
    port: int = _HUIDU_PORT
    device_ids: list[str] = field(default_factory=list)

    @property
    def base_url(self) -> str:
        """URL base del gateway (es. ``"http://192.168.1.33:30080"``)."""
        return f"http://{self.host}:{self.port}"


def _get_local_subnet() -> ipaddress.IPv4Network:
    """Rileva automaticamente la subnet locale del PC.

    Si connette a Google DNS (senza inviare dati) per determinare
    l'interfaccia di rete attiva, poi calcola la subnet /24.

    Returns:
        Rete IPv4 /24 (es. ``192.168.1.0/24``).

    Raises:
        OSError: Se non è possibile determinare l'interfaccia locale.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]

    # Calcola la subnet /24 dall'IP locale
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    logger.info("Subnet locale rilevata: %s (IP locale: %s)", network, local_ip)
    return network


def _tcp_port_open(host: str, port: int, timeout: float) -> bool:
    """Verifica se una porta TCP è aperta su un host.

    Args:
        host: Indirizzo IP da testare.
        port: Porta TCP da testare.
        timeout: Timeout in secondi per la connessione.

    Returns:
        ``True`` se la porta è aperta e risponde.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _verify_huidu_gateway(
    host: str,
    port: int,
    sdk_key: str,
    sdk_secret: str,
) -> DiscoveredGateway | None:
    """Verifica che un host sia un gateway Huidu valido.

    Chiama ``GET /api/device/list/`` e controlla la risposta.

    Args:
        host: IP del gateway.
        port: Porta del gateway.
        sdk_key: Chiave SDK per l'autenticazione.
        sdk_secret: Segreto SDK per la firma HMAC.

    Returns:
        ``DiscoveredGateway`` se l'host è un gateway Huidu, ``None`` altrimenti.
    """
    url = f"http://{host}:{port}/api/device/list/"
    signer = AuthSigner(sdk_key=sdk_key, sdk_secret=sdk_secret)
    headers = signer.sign_request(body="")
    try:
        resp = requests.get(url, headers=headers, timeout=_HTTP_VERIFY_TIMEOUT)
        if not resp.ok:
            return None
        data = resp.json()
        if data.get("message") != "ok":
            return None
        device_ids: list[str] = data.get("data", [])
        if not isinstance(device_ids, list):
            device_ids = []
        logger.info(
            "Gateway Huidu trovato: %s:%d — %d controller connessi",
            host,
            port,
            len(device_ids),
        )
        return DiscoveredGateway(host=host, port=port, device_ids=device_ids)
    except Exception:
        return None


def _scan_host(
    host: str,
    port: int,
    sdk_key: str,
    sdk_secret: str,
    connect_timeout: float,
) -> DiscoveredGateway | None:
    """Scansiona un singolo host: check TCP poi verifica Huidu.

    Args:
        host: IP da testare.
        port: Porta da testare.
        sdk_key: Chiave SDK.
        sdk_secret: Segreto SDK.
        connect_timeout: Timeout per il check TCP.

    Returns:
        ``DiscoveredGateway`` se trovato, ``None`` altrimenti.
    """
    if not _tcp_port_open(host, port, connect_timeout):
        return None
    logger.debug("Porta %d aperta su %s — verifica Huidu...", port, host)
    return _verify_huidu_gateway(host, port, sdk_key, sdk_secret)


def discover_gateways(
    sdk_key: str,
    sdk_secret: str,
    *,
    subnet: str | None = None,
    port: int = _HUIDU_PORT,
    connect_timeout: float = _CONNECT_TIMEOUT,
    max_workers: int = _MAX_WORKERS,
) -> list[DiscoveredGateway]:
    """Scopre tutti i gateway Huidu sulla subnet locale.

    Scansiona in parallelo tutti gli indirizzi della subnet /24,
    verifica la porta TCP e autentica ogni gateway trovato.

    Args:
        sdk_key: Chiave SDK Huidu (da ``.env``).
        sdk_secret: Segreto SDK Huidu (da ``.env``).
        subnet: Subnet CIDR da scansionare (es. ``"192.168.1.0/24"``).
                Se ``None``, viene rilevata automaticamente.
        port: Porta del gateway (default ``30080``).
        connect_timeout: Timeout TCP per host in secondi (default ``0.5``).
        max_workers: Thread paralleli per lo scan (default ``64``).

    Returns:
        Lista di ``DiscoveredGateway`` trovati (può essere vuota).

    Example::

        gateways = discover_gateways(sdk_key="k", sdk_secret="s")
        for gw in gateways:
            print(f"{gw.host}: {gw.device_ids}")
    """
    if subnet:
        network = ipaddress.IPv4Network(subnet, strict=False)
    else:
        try:
            network = _get_local_subnet()
        except OSError as exc:
            logger.error("Impossibile rilevare la subnet locale: %s", exc)
            return []

    hosts = list(network.hosts())
    logger.info(
        "Avvio scan su %s — %d host, porta %d, %d thread",
        network,
        len(hosts),
        port,
        max_workers,
    )

    found: list[DiscoveredGateway] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _scan_host,
                str(host),
                port,
                sdk_key,
                sdk_secret,
                connect_timeout,
            ): host
            for host in hosts
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                found.append(result)

    logger.info("Scan completato: %d gateway trovati.", len(found))
    found.sort(key=lambda gw: ipaddress.IPv4Address(gw.host))
    return found
