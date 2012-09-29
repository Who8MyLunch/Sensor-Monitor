

from __future__ import division, print_function, unicode_literals

import _gpio

############################################

# Constants.
LOW = 0
HIGH = 1

MODE_PINS  = 0
MODE_GPIO = 1
MODE_SYS = 2
MODE_PIFACE = 3

INPUT = 0
OUTPUT = 1
PWM_OUTPUT = 2

PUD_OFF = 0
PUD_DOWN = 1
PUD_UP = 2

PWM_MODE_MS = 0
PWM_MODE_BAL = 1

################################3333

# Python extensions for wiringPi library functions.
def wiringPiSetup():
    """
    This initialises the wiringPi system and assumes that the calling program is going
    to be using the wiringPi pin numbering scheme. This is a simplified numbering scheme
    which provides a mapping from virtual pin numbers 0 through 16 to the real underlying
    Broadcom GPIO pin numbers. See the pins page for a table which maps the wiringPi pin
    number to the Broadcom GPIO pind number to the physical location on the edge connector.

    This function needs to be called with root privileges.
    """
    return _gpio._wiringPiSetup()


def wiringPiSetupGpio():
    """
    Identical to wiringPiSetup, except it allows the calling programs to use the
    Broadcom GPIO pin numbers directly with no re-mapping.
    """
    return _gpio._wiringPiSetupGpio()


def wiringPiSetupSys():
    """
    """
    return _gpio._wiringPiSetupSys()


def wiringPiSetupPiFace():
    """
    This initialises the wiringPi system but uses the /sys/class/gpio interface
    rather than accessing the hardware directly. This can be called as a non-root
    user provided the GPIO pins have been exported before-hand using the gpio
    program. Pin number in this mode is the native Broadcom GPIO numbers.

    Note: In this mode you can only use the pins which have been exported via the
    /sys/class/gpio interface. You must export these pins before you call your
    program. You can do this in a separate shell-script, or by using the
    system() function from inside your program.

    Also note that some functions (noted below) have no effect when using this
    mode as they're not currently possible to action unless called with root priveledges.
    """
    return _gpio._wiringPiSetupPiFace()


def pinMode(pin, mode):
    """
    This sets the mode of a pin to either INPUT, OUTPUT, or PWM_OUTPUT. Note that
    only wiringPi pin 1 (GPIO-18) supports PWM output. The pin number is the number
    obtained from the pins table.

    This function has no effect when in Sys mode.
    """
    _gpio._pinMode(pin, mode)


def pullUpDnControl(pin, pud):
    """
    This sets the pull-up or pull-down resistor mode on the given pin, which should
    be set as an input. Unlike the Arduino, the BCM2835 has both pull-up an down
    internal resistors. The parameter pud should be; PUD_OFF, (no pull up/down),
    PUD_DOWN (pull to ground) or PUD_UP (pull to 3.3v)

    This function has no effect when in Sys mode (see above) If you need to activate
    a pull-up/pull-down, then you can do it with the gpio program in a script before
    you start your program.
    """
    _gpio._pullUpDnControl(pin, pud)


def digitalWrite(pin, value):
    """
    Writes the value HIGH or LOW (1 or 0) to the given pin which must have been
    previously set as an output.
    """
    _gpio._digitalWrite(pin, value)


def digitalRead(pin):
    """
    This function returns the value read at the given pin. It will be HIGH or
    LOW (1 or 0) depending on the logic level at the pin.
    """
    return _gpio._digitalRead(pin)



# def setPadDrive(group, value):
    # """
    # """
    # _gpio._setPadDrive(group, value)


def delayMicroseconds(howLong):
    """
    This causes program execution to pause for at least howLong microseconds.
    Due to the multi-tasking nature of Linux it could be longer. Note that the
    maximum delay is an unsigned 32-bit integer microseconds or approximately
    71 minutes.
    """
    _gpio._delayMicroseconds(howLong)


def millis():
    """
    This returns a number representing the number if millisenconds since your
    program called one of the wiringPiSetup functions. It returns an unsigned
    32-bit number which wraps after 49 days.
    """
    return _gpio.millis()



def pwmWrite(pin, value):
    """
    Writes the value to the PWM register for the given pin. The value must be
    between 0 and 1024. (Again, note that only pin 1 supports PWM)

    This function has no effect when in Sys mode (see above).
    """
    _gpio._pwmWrite(pin, value)


def pwmSetMode(mode):
    """
    """
    _gpio._pwmSetMode(mode)


def pwmSetRange(range):
    """
    """
    _gpio._pwmSetRange(range)

