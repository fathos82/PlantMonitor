import logging
import subprocess
import signal
from typing import Optional

logger = logging.getLogger("CAMERA")


class StreamPublisher:
    def __init__(
        self,
        source: str,
        destination_rtmp: str,
        source_type: str = "usb",  # "usb" | "ip"
        video_size: str = "1280x720",
        framerate: int = 30,
        reencode: bool = True,
    ):
        """
        source:
            USB  -> /dev/v4l/by-id/usb-XXXX
            IP   -> rtsp://user:pass@ip:554/stream

        destination_rtmp:
            rtmp://IP:1935/path
        """
        self.source = source
        self.destination_rtmp = destination_rtmp
        self.source_type = source_type
        self.video_size = video_size
        self.framerate = framerate
        self.reencode = reencode
        self.process: Optional[subprocess.Popen] = None

    def _build_ffmpeg_cmd(self) -> list[str]:
        cmd = ["ffmpeg", "-loglevel", "info"]

        # ---------- INPUT ----------
        if self.source_type == "usb":
            cmd += [
                "-f", "v4l2",
                "-video_size", self.video_size,
                "-framerate", str(self.framerate),
                "-i", self.source,
            ]
        elif self.source_type == "ip":
            cmd += [
                "-rtsp_transport", "tcp",
                "-i", self.source,
            ]
        else:
            logger.error("source_type deve ser 'usb' ou 'ip'")
            raise ValueError("source_type deve ser 'usb' ou 'ip'")

        # ---------- VIDEO ----------
        if self.reencode:
            cmd += [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-tune", "zerolatency",
            ]
        else:
            cmd += ["-c:v", "copy"]

        # ---------- AUDIO ----------
        cmd += ["-an"]

        # ---------- OUTPUT ----------
        cmd += [
            "-f", "flv",
            self.destination_rtmp,
        ]

        return cmd

    def start(self):
        if self.is_running():
            raise RuntimeError("Stream já está rodando")

        self.process = None  # limpa referência de processo morto

        cmd = self._build_ffmpeg_cmd()

        logger.info("Iniciando stream da fonte: %s", self.source)
        logger.info("CMD: %s", " ".join(cmd))

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self):
        if not self.process:
            return

        logger.info("Parando stream...")
        self.process.send_signal(signal.SIGINT)
        self.process.wait()
        self.process = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None