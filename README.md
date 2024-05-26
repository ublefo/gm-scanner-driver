# UART Barcode Scanner Driver

A simple driver module to make interfacing with serial barcode scanner modules easier. The driver takes care of all the setup work and contains sane defaults. Right now support is limited to modules from Grow, and a lot of the registers aren't exposed. Support for other vendors' modules may be implemented at a future date. This driver will be published to PyPI at some point, I just haven't had the time to do it yet.

## Tested modules

- Grow GM65 or GM65-S
- Grow GM812

## Untested modules that will probably work

- This is just a GM65-S with a better breakout board: https://www.waveshare.com/barcode-scanner-module.htm

## Setup

1. Scan the factory reset code
2. Scan the USB Serial code to switch module into USB CDC ACM mode

## Usage

```py
    scanner_object = scanner.Scanner("/dev/ttyACM0")
    scanner_object.configure()
    scanner_object.disable_all_formats()
    scanner_object.enable_format(scanner.GM65FormatRegister.QR)
    scanner_object.enable_format(scanner.GM65FormatRegister.DATAMATRIX)
    # Do not call this all the time since it writes to flash memory
    # scanner_object.save_config()

    # scan() returns NAK (0x15) if decode has timed out
    print(scanner_object.scan())

```


## Caveats

1. The GM812 doesn't expose the registers for RF message config over UART, so you will have to set up the RF messages with the setup QR codes in the manual. This driver assumes the read fail message is `0x15` (NAK) `0x0D` (CR), so you will have to scan the code for editing RF message, scan the code `1, 5, 0, D` in the appendix of the manual, and finaly scan the code to save the config.
2. I really don't recommend getting the GM812 over the GM65 unless aesthetics are very important to you. It is marginally slower than the GM65 and the illumination LED is too bright, so it tends to over-expose the image when you're trying to read very tiny barcodes at a close distance.

## Notes

1. The GM65 takes about 10 seconds to switch to CDC ACM mode on first boot.
2. Grow modules can be sourced from [AliExpress](https://hzgrow.aliexpress.com). This project is not affiliated with any module vendors, I wrote it because I needed to use one of these in a test setup.
