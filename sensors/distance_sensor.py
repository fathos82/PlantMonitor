import time
from typing import List, Dict
import RPi.GPIO as GPIO
from sensors.sensors import AbstractSensor



class HCSR04DistanceSensor(AbstractSensor):
    sensor_name = "Ultrasonic Distance Sensor"
    model = "HC-SR04"
    capabilities = ['distance']

    def __init__(self, **kwargs):
        self.trigger_pin = kwargs.get('trigger_pin', 23)
        self.echo_pin = kwargs.get('echo_pin', 24)

    def setup(self) -> None:
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

        GPIO.output(self.trigger_pin, GPIO.LOW)
        time.sleep(0.05)
        self.is_ready = True

    def probe(self) -> bool:
        """
        Verifica se o sensor responde com um pulso de ECHO.
        Não valida distância exata, apenas presença.
        """
        if not self.is_initialized:
            self.setup()

        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)

        timeout = time.time() + 0.05

        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout:
                return False

        return True

    def read(self) -> Dict[str, float]:
        """
        Retorna a distância em centímetros.
        """
        print("[HC-SR04] Iniciando leitura")

        if not self.is_initialized:
            print("[HC-SR04] Sensor não inicializado, executando setup()")
            self.setup()

        # Pulso de trigger
        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)
        print("[HC-SR04] Trigger enviado")

        timeout_start = time.time() + 0.05
        timeout_end = time.time() + 0.05

        # Aguarda início do echo
        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout_start:
                print("[HC-SR04] Timeout aguardando início do ECHO")
                raise RuntimeError("Timeout aguardando ECHO (start)")

        start = time.time()
        print("[HC-SR04] ECHO iniciado")

        # Aguarda fim do echo
        while GPIO.input(self.echo_pin) == 1:
            if time.time() > timeout_end:
                print("[HC-SR04] Timeout aguardando fim do ECHO")
                raise RuntimeError("Timeout aguardando ECHO (end)")

        end = time.time()
        print("[HC-SR04] ECHO finalizado")

        duration = end - start
        distance_cm = (duration * 34300) / 2

        print(f"[HC-SR04] Distância: {distance_cm:.2f} cm")

        return {
            "distance_cm": round(distance_cm, 2),
            "timestamp": time.time()
        }

    @property
    def local_id(self) -> str:
        return f"distance:{self.trigger_pin}:{self.echo_pin}"