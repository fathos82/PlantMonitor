import struct
import time
from typing import Dict

import smbus2

from errors import SensorSetupError, SensorTimeoutError
from logs import get_logger
from sensors.base import AbstractSensor, SensorCapability, SensorModel
from utils import get_instant

logger = get_logger("SENSOR", sub="MQ135")

# ── Registradores do ADS1115 ───────────────────────────────────────────────
_REG_CONVERSION = 0x00
_REG_CONFIG = 0x01

# Bits do registrador de configuração (16-bit)
_OS_SINGLE = 0x8000  # Inicia conversão single-shot
_MODE_SINGLE = 0x0100  # Modo single-shot

# Multiplexador: canal single-ended (AINx vs GND)
_MUX = {
    0: 0x4000,  # AIN0
    1: 0x5000,  # AIN1
    2: 0x6000,  # AIN2
    3: 0x7000,  # AIN3
}

# PGA ±4.096V → FSR = 4.096V → 1 LSB ≈ 125µV
_PGA_4096 = 0x0600
_FSR_4096 = 4.096

# Data rate: 128 SPS (padrão — ~8 ms por conversão)
_DR_128SPS = 0x0080

# Timeout para aguardar fim da conversão single-shot
_CONVERSION_TIMEOUT_S = 0.1

# ── Calibração do MQ-135 ───────────────────────────────────────────────
# Resistência de carga (RL): 20kΩ (típico na maioria dos módulos MQ)
_RL_OHM = 20000.0

# Constantes de calibração para diferentes gases (fornecidas pelo datasheet)
# Formato: { "gas_name": (a, b) }
# Equação: ppm = a × (Rs/Ro)^b
_MQ135_CALIBRATION = {
    "CO2": (116.6020682, -2.769034857),  # Calibração para CO2
    "CO": (605.18, -3.937),  # Calibração para CO
    "NH4": (102.2, -2.473),  # Calibração para NH3
    "NO2": (1.15, -1.32),  # Calibração para NO2
    "C2H5OH": (77.5, -1.64),  # Calibração para etanol
    "CH4": (2.3, -0.64),  # Calibração para metano
    "LPG": (116.6, -2.86),  # Calibração para GLP
    "smoke": (44.5, -1.84),  # Calibração para fumaça
}

# Resistência sensor ao ar limpo (Ro): obtida na calibração
# Valor típico: 76kΩ, mas pode variar. Usar probe() para calibrar
_RO_OHM_DEFAULT = 76000.0

# Sensibilidade nominal do sensor: razão Rs/Ro ao ar limpo
# Normalmente ~0.9 quando o sensor é novo
_CALIBRATION_PPM_CO2 = 400.0  # CO2 padrão do ar limpo: ~400 ppm


class MQ135AirQualitySensor(AbstractSensor):
    sensor_name = "Air Quality Sensor"
    model = SensorModel.MQ135
    capabilities = [SensorCapability.AIR_QUALITY]
    interface = "I2C"

    def configure(self, **params) -> None:
        """
        Parâmetros esperados:
            - i2c_bus (int)       : Barramento I2C do Raspberry Pi (padrão: 1 → /dev/i2c-1)
            - i2c_address (int)   : Endereço I2C do ADS1115 (padrão: 0x48, pino ADDR → GND)
            - adc_channel (int)   : Canal do ADS1115 onde o MQ-135 está ligado (padrão: 0)
            - rl_ohm (float)      : Resistência de carga em Ohms (padrão: 20000)
            - ro_ohm (float)      : Resistência de referência Ro em Ohms (padrão: 76000)
            - calibration_gas (str): Gás usado para calibração (padrão: "CO2")

        Endereços disponíveis conforme pino ADDR do ADS1115:
            ADDR → GND : 0x48  (padrão)
            ADDR → VDD : 0x49
            ADDR → SDA : 0x4A
            ADDR → SCL : 0x4B

        Notas sobre calibração:
            O MQ-135 precisa de calibração em ar limpo para determinar Ro.
            Se ro_ohm não for fornecido, usa valor padrão (76000 Ω).
            Para melhor precisão, calibre em ar conhecido (ex: ar externo a ~400ppm CO2).
        """
        self.i2c_bus = int(params.get("i2c_bus", 1))
        self.i2c_address = params.get("i2c_address", 0x48)
        if isinstance(self.i2c_address, str):
            self.i2c_address = int(self.i2c_address, 0)

        self.adc_channel = int(params.get("adc_channel", 0))
        self.rl_ohm = float(params.get("rl_ohm", _RL_OHM))
        self.ro_ohm = float(params.get("ro_ohm", _RO_OHM_DEFAULT))
        self.calibration_gas = params.get("calibration_gas", "CO2").upper()

        if self.adc_channel not in _MUX:
            raise ValueError(f"adc_channel deve ser 0–3, recebido: {self.adc_channel}")

        if self.calibration_gas not in _MQ135_CALIBRATION:
            valid_gases = list(_MQ135_CALIBRATION.keys())
            raise ValueError(
                f"Gás '{self.calibration_gas}' não suportado. "
                f"Gases válidos: {valid_gases}"
            )

        logger.debug(
            "I2C: (bus=%s, address=0x%02X, channel=%s) | "
            "Calibração: (RL=%.0fΩ, Ro=%.0fΩ, gas=%s)",
            self.i2c_bus,
            self.i2c_address,
            self.adc_channel,
            self.rl_ohm,
            self.ro_ohm,
            self.calibration_gas,
        )

    def setup(self) -> None:
        logger.info("Iniciando setup do sensor MQ-135")

        try:
            self._bus = smbus2.SMBus(self.i2c_bus)
            time.sleep(0.05)

            self.is_initialized = True
            logger.info("Sensor MQ-135 inicializado com sucesso")

        except PermissionError as exc:
            logger.error("Permissão insuficiente para acessar barramento I2C")
            raise SensorSetupError(
                "Sensor indisponível por falta de permissão.",
                sensor_id=self.api_id,
            ) from exc

        except Exception as exc:
            logger.exception("Erro ao abrir barramento I2C")
            raise SensorSetupError(
                "Falha ao configurar barramento I2C do sensor.",
                sensor_id=self.api_id,
            ) from exc

    def probe(self) -> bool:
        """
        Verifica se o ADS1115 responde no endereço I2C configurado
        tentando ler o registrador de configuração.

        Retorna: True se o sensor foi detectado, False caso contrário
        """
        logger.debug("Executando probe do sensor MQ-135")

        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        try:
            self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            logger.debug("Probe bem-sucedido — ADS1115 encontrado em 0x%02X", self.i2c_address)
            return True

        except OSError:
            logger.warning("Probe falhou — ADS1115 não encontrado em 0x%02X", self.i2c_address)
            return False

        except Exception:
            logger.exception("Erro inesperado durante probe")
            return False

    def read(self) -> Dict[SensorCapability, float]:
        """
        Lê a voltagem do MQ-135 via ADS1115, calcula a resistência do sensor (Rs)
        e converte para ppm usando a curva de calibração do gás configurado.

        Fórmula:
            V_out (V) = raw × (FSR / 32767)
            Rs (Ω) = RL × (V_ref - V_out) / V_out
            ppm = a × (Rs/Ro)^b

        Retorna:
            - QUALITY: ppm estimado do gás configurado (0-500 típico)
            - STATUS: qualidade do ar em texto ("Boa", "Moderada", "Ruim", "Muito ruim")
            - measuredAt: timestamp da leitura
        """
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        raw = self._read_ads1115()

        # Converter raw para tensão (signed 16-bit)
        voltage_v = raw * (_FSR_4096 / 32767.0)

        # Calcular resistência do sensor (Rs)
        # Rs = RL × (V_ref - V_out) / V_out
        # Assumindo V_ref = 5V (típico em Arduino/Raspberry Pi com ADS1115)
        v_ref = 5.0
        if voltage_v >= v_ref:
            logger.warning("Leitura de voltagem saturada (%.4fV), usando valor máximo", voltage_v)
            voltage_v = v_ref - 0.001

        rs_ohm = self.rl_ohm * (v_ref - voltage_v) / voltage_v

        # Razão Rs/Ro
        ratio = rs_ohm / self.ro_ohm

        # Obter calibração do gás configurado
        a, b = _MQ135_CALIBRATION[self.calibration_gas]

        # Calcular ppm: ppm = a × (Rs/Ro)^b
        ppm = a * (ratio ** b)

        # Clampear ppm a valores razoáveis (0-500 ppm é típico)
        ppm = max(0, min(ppm, 5000))

        # Determinar qualidade qualitativa do ar baseado em ppm de CO2
        if self.calibration_gas == "CO2":
            quality_text = self._get_air_quality_text_co2(ppm)
        else:
            quality_text = self._get_air_quality_text_generic(ppm)

        logger.debug(
            "raw=%s | tensão=%.4fV | Rs=%.0fΩ | ratio=%.3f | ppm=%.1f | qualidade=%s",
            raw,
            voltage_v,
            rs_ohm,
            ratio,
            ppm,
            quality_text,
        )
        print(quality_text)
        return {
            SensorCapability.AIR_QUALITY: round(ppm, 2),
            # SensorCapability.STATUS: quality_text,
        }

    # ┌─────────────────────────────────────────────────────────────┐
    # │ Métodos privados: I2C                                       │
    # └─────────────────────────────────────────────────────────────┘

    def _read_ads1115(self) -> int:
        """
        Configura e dispara uma conversão single-shot no ADS1115.
        Aguarda o bit OS indicar conversão concluída e retorna
        o valor bruto signed de 16 bits.

        Retorna: valor raw signed 16-bit do conversor A/D
        """
        config = (
                _OS_SINGLE
                | _MUX[self.adc_channel]
                | _PGA_4096
                | _MODE_SINGLE
                | _DR_128SPS
        )

        high_byte = (config >> 8) & 0xFF
        low_byte = config & 0xFF
        self._bus.write_i2c_block_data(
            self.i2c_address, _REG_CONFIG, [high_byte, low_byte]
        )

        # Polling do bit OS (bit 15): OS=1 indica conversão concluída
        deadline = time.time() + _CONVERSION_TIMEOUT_S
        while True:
            data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            if data[0] & 0x80:
                break
            if time.time() > deadline:
                raise SensorTimeoutError(
                    "Timeout aguardando conversão do ADS1115",
                    sensor_id=self.api_id,
                )
            time.sleep(0.001)

        # Lê o registrador de conversão: 2 bytes big-endian signed
        data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONVERSION, 2)
        return struct.unpack(">h", bytes(data))[0]

    # ┌─────────────────────────────────────────────────────────────┐
    # │ Métodos privados: Calibração e qualidade                    │
    # └─────────────────────────────────────────────────────────────┘

    def _get_air_quality_text_co2(self, ppm: float) -> str:
        """
        Classifica a qualidade do ar baseado em concentração de CO2.
        Baseado em padrões ASHRAE (American Society of Heating, Refrigerating
        and Air-Conditioning Engineers).

        Intervalos:
            < 400 ppm    : Excelente
            400-1000 ppm : Boa
            1000-1500 ppm: Aceitável
            1500-2000 ppm: Moderada
            > 2000 ppm   : Ruim
        """
        if ppm < 400:
            return "Excelente"
        elif ppm < 1000:
            return "Boa"
        elif ppm < 1500:
            return "Aceitável"
        elif ppm < 2000:
            return "Moderada"
        else:
            return "Ruim"

    def _get_air_quality_text_generic(self, ppm: float) -> str:
        """
        Classificação genérica para outros gases (não-CO2).
        Baseada em percentual relativo da faixa esperada do sensor.
        """
        if ppm < 50:
            return "Excelente"
        elif ppm < 100:
            return "Boa"
        elif ppm < 200:
            return "Aceitável"
        elif ppm < 400:
            return "Moderada"
        else:
            return "Ruim"



    @property
    def local_id(self) -> str:
        """
        Identifica o sensor de forma única baseado em sua configuração física.

        Formato: "quality:mq135:i2cX:0xHH:C:gasY"
            X = barramento I2C
            HH = endereço I2C em hexadecimal
            C = canal do ADS1115
            Y = gás de calibração
        """
        local_id = (
            f"quality:mq135"
            f":i2c{self.i2c_bus}"
            f":0x{self.i2c_address:02X}"
            f":{self.adc_channel}"
            f":{self.calibration_gas.lower()}"
        )
        logger.debug("local_id gerado: %s", local_id)
        return local_id



    def shutdown(self) -> None:
        """Encerra a comunicação I2C e desliga o sensor."""
        logger.info("Desligando sensor MQ-135...")
        if hasattr(self, "_bus"):
            self._bus.close()