import time

import segno


def generate_qrcode_to_set_account(device_uuid):
    data = "plantmonitor://pair?token=" + device_uuid
    qr = segno.make(data)
    qr.terminal(border=2, compact=True)
    while True:  # todo: verify is_confirmed
        time.sleep(1)
