class LM35DZTemperatureSensor(AbstractSensor):
    sensor_name = "Analog Temperature Sensor"
    model = SensorModel.LM35DZ
    capabilities = [SensorCapability.TEMPERATURE]
    interface = "I2C"

    def read(self) -> Dict[SensorCapability, float]:
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        print("\n========== READ START ==========")
        print(self.__str__())

        print("\n--- TESTE MÉDIA (5 leituras) ---")
        values = []
        for i in range(5):
            v = self._read_ads1115()
            print(f"RAW[{i}]: {v}")
            values.append(v)
        avg = sum(values) / len(values)
        print(f"MÉDIA RAW: {avg}")

        print("\n--- LEITURA FINAL ---")
        raw = self._read_ads1115()
        print(f"RAW FINAL: {raw}")

        voltage_v = raw * (_FSR_2048 / 32767.0)
        print(f"VOLTAGE: {voltage_v}")

        temperature_c = (voltage_v * 1000.0) / _MV_PER_CELSIUS
        print(f"TEMP_CALCULADA: {temperature_c}")

        result = round(temperature_c, 2)
        print(f"TEMP_FINAL (round): {result}")

        print("========== READ END ==========\n")

        return {
            SensorCapability.TEMPERATURE: result,
            "measuredAt": get_instant(),
        }

    def _read_ads1115(self) -> int:
        print("\n[ADS1115] Iniciando leitura")

        config = (
            _OS_SINGLE
            | _MUX[self.adc_channel]
            | _PGA_2048
            | _MODE_SINGLE
            | _DR_128SPS
        )

        print(f"[ADS1115] CONFIG: 0x{config:04X}")

        high_byte = (config >> 8) & 0xFF
        low_byte  =  config       & 0xFF

        print(f"[ADS1115] WRITE BYTES: [{high_byte:#04x}, {low_byte:#04x}]")

        self._bus.write_i2c_block_data(
            self.i2c_address, _REG_CONFIG, [high_byte, low_byte]
        )

        deadline = time.time() + _CONVERSION_TIMEOUT_S

        while True:
            data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            cfg = (data[0] << 8) | data[1]

            print(f"[ADS1115] POLL CONFIG: 0x{cfg:04X}")

            if data[0] & 0x80:
                print("[ADS1115] Conversão pronta")
                break

            if time.time() > deadline:
                print("[ADS1115] TIMEOUT!")
                raise SensorTimeoutError(
                    "Timeout aguardando conversão do ADS1115",
                    sensor_id=self.api_id,
                )

            time.sleep(0.001)

        data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONVERSION, 2)
        print(f"[ADS1115] RAW BYTES: {data}")

        raw = struct.unpack(">h", bytes(data))[0]
        print(f"[ADS1115] RAW CONVERTIDO: {raw}")

        return raw

    def __str__(self) -> str:
        return (
            f"LM35DZTemperatureSensor(\n"
            f"  sensor_name={self.sensor_name},\n"
            f"  model={self.model},\n"
            f"  interface={self.interface},\n"
            f"  i2c_bus={getattr(self, 'i2c_bus', None)},\n"
            f"  i2c_address=0x{getattr(self, 'i2c_address', 0):02X},\n"
            f"  adc_channel={getattr(self, 'adc_channel', None)},\n"
            f"  is_initialized={getattr(self, 'is_initialized', False)},\n"
            f"  local_id={self.local_id if hasattr(self, 'i2c_bus') else None}\n"
            f")"
        )