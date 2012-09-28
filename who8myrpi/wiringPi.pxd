

cdef extern from 'wiringPi/wiringPi.h':
    cdef int wiringPiSetup()
    cdef int wiringPiSetupSys()
    cdef int wiringPiSetupGpio()
    # cdef int wiringPiSetupPiFace()

    cdef void pinMode(int pin, int mode)
    cdef void pullUpDnControl(int pin, int pud)
    cdef void digitalWrite(int pin, int value)
    cdef void pwmWrite(int pin, int value)
    cdef void setPadDrive(int group, int value)
    cdef int  digitalRead(int pin)
    cdef void delayMicroseconds(unsigned int howLong)
    cdef void pwmSetMode(int mode)
    cdef void pwmSetRange(unsigned int range)



