import serial, time, sys, re
from xmodem import XMODEM
import serials_find
import SerialHelper

SCRIPT_DEBUG = 0


class PassthroughEnabled(Exception):
    pass

class PassthroughFailed(Exception):
    pass


def dbg_print(line=''):
    sys.stdout.write(line + '\n')
    sys.stdout.flush()


def _validate_serialrx(rl, config, expected):
    found = False
    if type(expected) == str:
        expected = [expected]
    rl.set_delimiters(["# "])
    rl.clear()
    rl.write("get serialrx_%s\r\n" % config)
    line = rl.read_line(1.).strip()
    for key in expected:
        key = " = %s" % key
        if key in line:
            found = True
            break
    return found


def bf_passthrough_init(port, requestedBaudrate, half_duplex=False):
    debug = SCRIPT_DEBUG

    sys.stdout.flush()
    dbg_print("======== PASSTHROUGH INIT ========")
    dbg_print("  Trying to initialize %s @ %s" % (port, requestedBaudrate))

    s = serial.Serial(port=port, baudrate=115200,
        bytesize=8, parity='N', stopbits=1,
        timeout=1, xonxoff=0, rtscts=0)

    rl = SerialHelper.SerialHelper(s, 3., ['CCC', "# "])
    rl.clear()
    # Send start command '#'
    rl.write("#\r\n", half_duplex)
    start = rl.read_line(2.).strip()
    #dbg_print("BF INIT: '%s'" % start.replace("\r", ""))
    if "CCC" in start:
        raise PassthroughEnabled("Passthrough already enabled and bootloader active")
    elif not start or not start.endswith("#"):
        raise PassthroughEnabled("No CLI available. Already in passthrough mode?")

    serial_check = []
    if not _validate_serialrx(rl, "provider", [["CRSF", "ELRS"], "GHST"][half_duplex]):
        serial_check.append("serialrx_provider != CRSF")
    if not _validate_serialrx(rl, "inverted", "OFF"):
        serial_check.append("serialrx_inverted != OFF")
    if not _validate_serialrx(rl, "halfduplex", ["OFF", "AUTO"]):
        serial_check.append("serialrx_halfduplex != OFF/AUTO")

    if serial_check:
        error = "\n\n [ERROR] Invalid serial RX configuration detected:\n"
        for err in serial_check:
            error += "    !!! %s !!!\n" % err
        error += "\n    Please change the configuration and try again!\n"
        dbg_print(error)
        raise PassthroughFailed(error)

    SerialRXindex = ""

    dbg_print("\nAttempting to detect FC UART configuration...")

    rl.set_delimiters(["\n"])
    rl.clear()
    rl.write("serial\r\n")

    while True:
        line = rl.read_line().strip()
        #print("FC: '%s'" % line)
        if not line or "#" in line:
            break

        if line.startswith("serial"):
            if debug:
                dbg_print("  '%s'" % line)
            config = re.search('serial ([0-9]+) ([0-9]+) ', line)
            if config and config.group(2) == "64":
                dbg_print("    ** Serial RX config detected: '%s'" % line)
                SerialRXindex = config.group(1)
                if not debug:
                    break

    if not SerialRXindex:
        raise PassthroughFailed("!!! RX Serial not found !!!!\n  Check configuration and try again...")

    cmd = "serialpassthrough %s %s" % (SerialRXindex, requestedBaudrate, )

    dbg_print("Enabling serial passthrough...")
    dbg_print("  CMD: '%s'" % cmd)
    rl.write(cmd + '\n')
    time.sleep(.2)
    s.close()

    dbg_print("======== PASSTHROUGH DONE ========")


if __name__ == '__main__':
    try:
        requestedBaudrate = int(sys.argv[1])
    except:
        requestedBaudrate = 420000
    port = serials_find.get_serial_port()
    try:
        bf_passthrough_init(port, requestedBaudrate)
    except PassthroughEnabled as err:
        dbg_print(str(err))
