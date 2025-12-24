import time

from utils import register_device, generate_qrcode


#
# sudo apt update
# sudo apt install --reinstall ca-certificates
# sudo update-ca-certificates
# pip install --upgrade pip setuptools wheel


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