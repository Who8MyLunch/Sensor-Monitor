
Ideas for Sensors
=================

Currently module sensors.py is too complicated.  Incorporating new Kalman filter in this mess would
just make it worse.  Time to do some refactoring.  I like the idea of having a `Channel` as the top-
level class that is used by my application.  The plan is to split it up into several nested
components and to leverage the use of generators.  The current version has some extra stuff added
later to handle making sure that a group of sensors has started running properely.  Some of those
functions can be made easier to implement if I think carefully about what goes inside the new
refactored classes.

Starting with the inner-most layer:

    1. **Channel_Raw**:  A generator that yields data read from sensor using `read_dht22_single`.
    Potentially have methods to test that sensor is correctly connected.  Knows about waiting a
    predetermined amount of time between calls to request data.  Knows about initial wait time for
    sensor to power up.  This could be based on what I currently have in the class `Channel`.

    2. **Channel_Filter**: A generator instanciated with a `Reader` object.  Receive 'raw' data from
    sensor `Reader` and process those signals through a Kalman filter.  Yield nice data to the next
    layer in the process.  Knows how to wait a bit at the beggining to collect sufficient data for
    estimating data statistics.

    3. **Collecter**: Initialized with a list of ready-to-go data generators.  See this cool module
    I found: gen_multi.py.
