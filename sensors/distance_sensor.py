import time
from typing import Dict
import RPi.GPIO as GPIO

from errors import SensorSetupError, SensorTimeoutError
from sensors.sensors import AbstractSensor


# todo: change logs


class HCSR04DistanceSensor(AbstractSensor):
    sensor_name = "Ultrasonic Distance Sensor"
    model = "HC-SR04"
    capabilities = ['distance']

    def __init__(self, **kwargs):
        print("[HC-SR04][INIT] Inicializando sensor com parâmetros:", kwargs)
        self.set_params(**kwargs)
        print(f"[HC-SR04][INIT] trigger_pin={self.trigger_pin}, echo_pin={self.echo_pin}")

    def set_params(self, **kwargs) -> None:
        self.trigger_pin = int(kwargs.get('trigger_pin', 23))
        self.echo_pin = int(kwargs.get('echo_pin', 24))

    def setup(self) -> None:
        try:
            print("[HC-SR04][SETUP] Iniciando setup do sensor")

            GPIO.setmode(GPIO.BCM)
            print("[HC-SR04][SETUP] GPIO mode setado para BCM")

            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            print("[HC-SR04][SETUP] GPIO pins configurados")

            GPIO.output(self.trigger_pin, GPIO.LOW)
            print("[HC-SR04][SETUP] Trigger setado para LOW")

            time.sleep(0.05)

            self.is_initialized = True
            print("[HC-SR04][SETUP] Sensor inicializado com sucesso")
        except PermissionError as e:
            print(e)
            raise SensorSetupError("Sensor indisponível por falta de permissão.", sensor_id= self.api_id) from e
        except RuntimeError as e:
            print(e)
            raise SensorSetupError("Ambiente incompatível com o sensor.", sensor_id= self.api_id) from e
        except Exception as e:
            print(e)
            raise SensorSetupError("Falha inesperada na inicialização do sensor.", sensor_id= self.api_id) from e

    def probe(self) -> bool:
        """
        Verifica se o sensor responde com um pulso de ECHO.
        """
        print("[HC-SR04][PROBE] Iniciando probe do sensor")

        if not self.is_initialized:
            print("[HC-SR04][PROBE] Sensor não inicializado, chamando setup()")
            self.setup()

        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)
        print("[HC-SR04][PROBE] Trigger enviado")

        timeout = time.time() + 0.05

        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout:
                print("[HC-SR04][PROBE] Timeout aguardando resposta do ECHO")
                return False

        print("[HC-SR04][PROBE] Sensor respondeu com ECHO")
        return True

    def read(self) -> Dict[str, float]:
        """
        Retorna a distância em centímetros.
        """
        print("[HC-SR04][READ] Iniciando leitura")

        if not self.is_initialized:
            print("[HC-SR04][READ] Sensor não inicializado, executando setup()")
            self.setup()

        # Pulso de trigger
        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)
        print("[HC-SR04][READ] Trigger enviado")

        timeout_start = time.time() + 0.05
        timeout_end = time.time() + 0.05

        # Aguarda início do echo
        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout_start:
                print("[HC-SR04][READ][ERRO] Timeout aguardando início do ECHO")
                # todo melhorar essa mensagem de timeout
                raise SensorTimeoutError("Timeout aguardando ECHO (start)", sensor_id=self.api_id)

        start = time.time()
        print("[HC-SR04][READ] ECHO iniciado")
        # Aguarda fim do echo
        while GPIO.input(self.echo_pin) == 1:
            if time.time() > timeout_end:
                print("[HC-SR04][READ][ERRO] Timeout aguardando fim do ECHO")
                raise SensorTimeoutError("Timeout aguardando ECHO (end)", sensor_id=self.api_id)
        end = time.time()
        print("[HC-SR04][READ] ECHO finalizado")

        duration = end - start
        distance_cm = (duration * 34300) / 2

        print(f"[HC-SR04][READ] Distância calculada: {distance_cm:.2f} cm")

        return {
            "distance_cm": round(distance_cm, 2),
            "timestamp": time.time()
        }

    @property
    def local_id(self) -> str:
        local_id = f"distance:{self.trigger_pin}:{self.echo_pin}"
        print(f"[HC-SR04][LOCAL_ID] local_id={local_id}")
        return local_id

    def shutdown(self) -> None:
        raise NotImplemented
