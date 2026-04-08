import struct
import time
from typing import Dict

import smbus2

from errors import SensorSetupError, SensorTimeoutError
from logs import get_logger
from sensors.base import AbstractSensor, SensorCapability, SensorModel
from utils import get_instant

logger = get_logger("SENSOR", sub="LM35DZ")

# ── Registradores do ADS1115 ───────────────────────────────────────────────
_REG_CONVERSION = 0x00
_REG_CONFIG     = 0x01

# Bits do registrador de configuração (16-bit)
_OS_SINGLE   = 0x8000  # Inicia conversão single-shot
_MODE_SINGLE = 0x0100  # Modo single-shot

# Multiplexador: canal single-ended (AINx vs GND)
_MUX = {
    0: 0x4000,  # AIN0
    1: 0x5000,  # AIN1
    2: 0x6000,  # AIN2
    3: 0x7000,  # AIN3
}

# PGA ±6.144 V → FSR = 6.144 V → 1 LSB ≈ 187.5 µV
# Com 5V e LM35DZ saindo no máximo ~1V (100°C), ±6.144V cobre com folga
_PGA_2048 = 0x0400
_FSR_2048 = 2.048

# Data rate: 128 SPS (padrão — ~8 ms por conversão)
_DR_128SPS = 0x0080

# Timeout para aguardar fim da conversão single-shot
_CONVERSION_TIMEOUT_S = 0.1

# Sensibilidade do LM35DZ: 10 mV/°C
_MV_PER_CELSIUS = 10.0


class LM35DZTemperatureSensor(AbstractSensor):
    sensor_name = "Analog Temperature Sensor"
    model = SensorModel.LM35DZ
    capabilities = [SensorCapability.TEMPERATURE]
    interface = "I2C"

    def configure(self, **params) -> None:
            """
            Parâmetros esperados:
                - i2c_bus (int)    : Barramento I2C do Raspberry Pi (padrão: 1 → /dev/i2c-1)
                - i2c_address (int): Endereço I2C do ADS1115 (padrão: 0x48, pino ADDR → GND)
                - adc_channel (int): Canal do ADS1115 onde o LM35DZ está ligado (padrão: 0)

            Endereços disponíveis conforme pino ADDR do ADS1115:
                ADDR → GND : 0x48  (padrão)
                ADDR → VDD : 0x49
                ADDR → SDA : 0x4A
                ADDR → SCL : 0x4B
            """
            self.i2c_bus     = int(params.get("i2c_bus", 1))
            self.i2c_address  = params.get("i2c_address", 0x48)
            if isinstance(self.i2c_address, str):
                self.i2c_address = int(self.i2c_address, 0)

            self.adc_channel = int(params.get("adc_channel", 0))

            if self.adc_channel not in _MUX:
                raise ValueError(f"adc_channel deve ser 0–3, recebido: {self.adc_channel}")

            logger.debug(
                "I2C: (bus=%s, address=0x%02X, channel=%s)",
                self.i2c_bus,
                self.i2c_address,
                self.adc_channel,
            )

    def setup(self) -> None:
        logger.info("Iniciando setup do sensor")

        try:
            self._bus = smbus2.SMBus(self.i2c_bus)
            time.sleep(0.05)

            self.is_initialized = True
            logger.info("Sensor inicializado com sucesso")

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
        """
        logger.debug("Executando probe do sensor")

        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        try:
            self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            logger.debug("Probe bem-sucedido")
            return True

        except OSError:
            logger.warning("Probe falhou — ADS1115 não encontrado em 0x%02X", self.i2c_address)
            return False

        except Exception:
            logger.exception("Erro inesperado durante probe")
            return False

    def read(self) -> Dict[SensorCapability, float]:
        """
        Dispara uma conversão single-shot no ADS1115, aguarda o resultado
        e retorna a temperatura em graus Celsius.

        Fórmula:
            V_out (V) = raw × (FSR / 32767)
            T (°C)    = (V_out × 1000) / 10
        """
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        print("\n" + "=" * 50)
        print(f"[READ] Canal ADC : {self.adc_channel} | Endereço: 0x{self.i2c_address:02X} | FSR: ±{_FSR_2048}V")

        # ── Coleta de amostras brutas para diagnóstico ─────────────────────
        NUM_SAMPLES = 7
        samples = []
        print(f"[AMOSTRAS] Coletando {NUM_SAMPLES} leituras brutas consecutivas:")

        for i in range(NUM_SAMPLES):
            raw_i = self._read_ads1115()
            v_i = raw_i * (_FSR_2048 / 32767.0)
            t_i = (v_i * 1000.0) / _MV_PER_CELSIUS
            samples.append(raw_i)
            print(f"  [{i + 1}/{NUM_SAMPLES}] raw={raw_i:6d}  tensão={v_i:.4f}V  temp={t_i:.2f}°C")
            time.sleep(0.012)  # pausa > período de conversão (128 SPS = ~7.8 ms)

        # ── Estatísticas ───────────────────────────────────────────────────
        raw_min = min(samples)
        raw_max = max(samples)
        raw_range = raw_max - raw_min
        raw_mean = sum(samples) / len(samples)

        lsb_to_celsius = (_FSR_2048 / 32767.0) * 1000.0 / _MV_PER_CELSIUS

        print(f"[ESTATÍSTICAS]")
        print(f"  Mínimo : raw={raw_min:6d}  → {raw_min * lsb_to_celsius:.2f}°C")
        print(f"  Máximo : raw={raw_max:6d}  → {raw_max * lsb_to_celsius:.2f}°C")
        print(f"  Média  : raw={raw_mean:7.1f}  → {raw_mean * lsb_to_celsius:.2f}°C")
        print(f"  Range  : {raw_range} LSBs  →  variação de {raw_range * lsb_to_celsius:.2f}°C entre amostras")

        # ── Diagnóstico de flutuação ───────────────────────────────────────
        FLUCT_WARN_LSB = 10  # ~0.06°C com PGA±2.048V — acima disso é suspeito
        FLUCT_CRIT_LSB = 50  # ~0.31°C — acima disso é problema claro

        if raw_range >= FLUCT_CRIT_LSB:
            print(f"[!! FLUTUAÇÃO CRÍTICA !!] {raw_range} LSBs — verifique:")
            print(f"  → GND do LM35DZ e GND do ADS1115 no mesmo ponto")
            print(f"  → Capacitor 100nF entre VDD e GND do ADS1115")
            print(f"  → Cabo analógico longo ou sem blindagem")
            print(f"  → Fonte de alimentação instável")
            logger.warning("Flutuação crítica detectada: range=%d LSBs (%.2f°C)", raw_range, raw_range * lsb_to_celsius)
        elif raw_range >= FLUCT_WARN_LSB:
            print(f"[! FLUTUAÇÃO ELEVADA] {raw_range} LSBs — ruído moderado presente")
            logger.warning("Flutuação elevada: range=%d LSBs (%.2f°C)", raw_range, raw_range * lsb_to_celsius)
        else:
            print(f"[✓ ESTÁVEL] Range de {raw_range} LSBs dentro do esperado")

        # ── Leitura final ──────────────────────────────────────────────────
        raw = self._read_ads1115()
        print(f"[LEITURA FINAL] raw={raw}")

        if raw < 0:
            print(f"[⚠ RAW NEGATIVO] raw={raw} → ruído próximo ao GND, clampando para 0")
            logger.warning("raw negativo (%s) clampado para 0 — possível problema de GND", raw)
            raw = 0

        voltage_v = raw * (_FSR_2048 / 32767.0)
        temperature_c = (voltage_v * 1000.0) / _MV_PER_CELSIUS

        print(f"[RESULTADO]  tensão={voltage_v:.4f}V  temperatura={temperature_c:.2f}°C")
        print("=" * 50 + "\n")

        logger.debug(
            "raw=%s  tensão=%.4fV  temperatura=%.2f°C",
            raw,
            voltage_v,
            temperature_c,
        )

        return {
            SensorCapability.TEMPERATURE: round(temperature_c, 2),
            "measuredAt": get_instant(),
        }
    # ------------------------------------------------------------------ #
    # I2C privado                                                          #
    # ------------------------------------------------------------------ #

    def _read_ads1115(self) -> int:
        """
        Configura e dispara uma conversão single-shot no ADS1115.
        Aguarda o bit OS indicar conversão concluída e retorna
        o valor bruto signed de 16 bits.
        """
        config = (
            _OS_SINGLE
            | _MUX[self.adc_channel]
            | _PGA_2048
            | _MODE_SINGLE
            | _DR_128SPS
        )

        high_byte = (config >> 8) & 0xFF
        low_byte  =  config       & 0xFF
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

    # ------------------------------------------------------------------ #
    # Identidade                                                           #
    # ------------------------------------------------------------------ #

    @property
    def local_id(self) -> str:
        local_id = (
            f"temperature:lm35dz"
            f":i2c{self.i2c_bus}"
            f":0x{self.i2c_address:02X}"
            f":{self.adc_channel}"
        )
        logger.debug("local_id gerado: %s", local_id)
        return local_id

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                        #
    # ------------------------------------------------------------------ #

    def shutdown(self) -> None:
        logger.info("Desligando sensor...")
        if hasattr(self, "_bus"):
            self._bus.close()