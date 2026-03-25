import requests
from requests import RequestException

from logs import get_logger
from settings import DEVICE_API_URL, SENSOR_API_URL, SENSOR_ERROR_API_URL

logger = get_logger("API_CLIENT")


def register_device(device_uuid: str, payload: dict) -> None:
    """
    Registra o device na API.
    Levanta SystemExit se a comunicação falhar — sem device registrado não há operação.
    """
    print("OIIIII")
    logger.info("Enviando dados do dispositivo para a API")

    try:
        response = requests.post(DEVICE_API_URL, json=payload, timeout=5)

        if response.status_code in (200, 201):
            logger.info("Dispositivo registrado com sucesso na API")
        else:
            logger.critical(
                "API respondeu com erro (%s): %s",
                response.status_code,
                response.text,
            )
            raise SystemExit(1)

    except RequestException:
        logger.critical("Falha ao comunicar com a API durante registro do device")
        raise SystemExit(1)


def get_sensors(device_uuid: str, since=None) -> list:
    """
    Retorna a lista de sensores associados ao device.
    Retorna [] em caso de falha para não quebrar o loop do pool.
    """
    logger.debug(
        "Requisitando sensores da API",
        extra={"device_uuid": device_uuid, "since": since},
    )

    try:
        response = requests.get(
            SENSOR_API_URL,
            params={"deviceUid": device_uuid},
            timeout=5,
        )

        if response.status_code in (200, 201):
            logger.debug("Sensores retornados com sucesso")
            return response.json()

        logger.warning(
            "API respondeu com status inesperado (%s)",
            response.status_code,
        )

    except RequestException:
        logger.error("Falha na comunicação com a API ao buscar sensores")

    return []


def send_sensor_error(sensor_id: int, message: str) -> None:
    """
    Reporta um erro de leitura de sensor para o backend.
    """
    url = SENSOR_ERROR_API_URL.format(sensor_id=sensor_id)
    logger.debug("Enviando erro do sensor (sensor_id=%s)", sensor_id)

    try:
        response = requests.post(url, json={"message": message}, timeout=5)

        if response.ok:
            logger.warning("Erro do sensor reportado (sensor_id=%s)", sensor_id)
        else:
            logger.error(
                "Falha ao reportar erro do sensor (sensor_id=%s, status=%s)",
                sensor_id,
                response.status_code,
            )

    except RequestException as e:
        logger.error(
            "Falha ao conectar na API para reportar erro do sensor (sensor_id=%s): %s",
            sensor_id,
            e,
        )