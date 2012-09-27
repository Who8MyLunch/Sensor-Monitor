

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
    
    
# Constants.    
cdef int WPI_MODE_PINS  = 0
cdef int WPI_MODE_GPIO = 1
cdef int WPI_MODE_GPIO_SYS = 2
cdef int WPI_MODE_PIFACE = 3

cdef int INPUT = 0
cdef int OUTPUT = 1
cdef int PWM_OUTPUT = 2

cdef int LOW = 0
cdef int HIGH = 1

cdef int PUD_OFF = 0
cdef int PUD_DOWN = 1
cdef int PUD_UP = 2

cdef int PWM_MODE_MS = 0
cdef int PWM_MODE_BAL = 1

