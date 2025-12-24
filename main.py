import time

from utils import register_device, generate_qrcode


def main():
    # todo: improve logs
    # todo: verify is exists qr code
    device_id = register_device()
    # generate from token, not uuid.
    generate_qrcode(device_id)
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()