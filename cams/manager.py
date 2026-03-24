from typing import List

from cams.stream_publisher import StreamPublisher
from logs import get_logger

logger = get_logger("CAMERA_MANAGER")


class CameraManager:
    def __init__(self):
        self._streams: List[StreamPublisher] = []

    def add(self, publisher: StreamPublisher):
        self._streams.append(publisher)
        publisher.start()
        logger.info("Stream adicionado e iniciado: %s", publisher.source)

    def remove(self, publisher: StreamPublisher):
        publisher.stop()
        self._streams.remove(publisher)
        logger.info("Stream removido: %s", publisher.source)

    def monitor(self):
        for publisher in self._streams:
            if not publisher.is_running():
                logger.warning("Stream caiu — reiniciando: %s", publisher.source)
                try:
                    publisher.start()
                except Exception:
                    logger.exception("Falha ao reiniciar stream: %s", publisher.source)


camera_manager = CameraManager()