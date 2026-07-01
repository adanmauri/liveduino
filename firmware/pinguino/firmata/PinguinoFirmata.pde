/*
 * PinguinoFirmata - a StandardFirmata-compatible firmware for 8-bit Pinguino
 * (PIC18F) boards.
 *
 * It implements the Firmata 2.x wire protocol on top of the Pinguino API, so
 * liveduino's native FirmataProtocol drives a Pinguino exactly as it does an
 * Arduino UNO. It aims for the full StandardFirmata feature surface:
 *
 *   - digital I/O, analog input, PWM
 *   - servo (SERVO_CONFIG + angle writes)
 *   - I2C master (config, write, one-shot read)
 *   - discovery: REPORT_FIRMWARE, CAPABILITY_QUERY, ANALOG_MAPPING_QUERY,
 *     PIN_STATE_QUERY
 *   - EXTENDED_ANALOG (PWM/servo on pins above 15)
 *   - SAMPLING_INTERVAL, STRING_DATA, SYSTEM_RESET
 *
 * Build & flash with the Pinguino IDE (8-bit / PIC18F). This is firmware, so it
 * cannot be unit-tested from the host; verify on a real board.
 *
 * ---------------------------------------------------------------------------
 * ADAPT to your board before flashing:
 *   1) The serial backend (USB CDC vs UART) in the "Serial backend" section.
 *   2) TOTAL_PINS / TOTAL_PORTS / TOTAL_ANALOG for your PIC18F model.
 *   3) The servo and I2C calls: the Pinguino Servo and I2C library APIs vary by
 *      version; the calls below are marked with "PINGUINO LIB" - verify them.
 * ---------------------------------------------------------------------------
 */

// ---- Board layout (adjust per PIC18F model) --------------------------------
#define TOTAL_PINS    30
#define TOTAL_PORTS   4          // ceil(TOTAL_PINS / 8)
#define TOTAL_ANALOG  13
#define ANALOG_BASE   17         // digital pin that carries analog channel 0

// ---- Firmata protocol constants --------------------------------------------
#define DIGITAL_MESSAGE          0x90
#define ANALOG_MESSAGE           0xE0
#define REPORT_ANALOG            0xC0
#define REPORT_DIGITAL           0xD0
#define SET_PIN_MODE             0xF4
#define SET_DIGITAL_PIN_VALUE    0xF5
#define REPORT_VERSION           0xF9
#define START_SYSEX              0xF0
#define END_SYSEX                0xF7
#define SYSTEM_RESET             0xFF

// Sysex sub-commands
#define SERIAL_MESSAGE           0x60
#define ANALOG_MAPPING_QUERY     0x69
#define ANALOG_MAPPING_RESPONSE  0x6A
#define CAPABILITY_QUERY         0x6B
#define CAPABILITY_RESPONSE      0x6C
#define PIN_STATE_QUERY          0x6D
#define PIN_STATE_RESPONSE       0x6E
#define EXTENDED_ANALOG          0x6F
#define SERVO_CONFIG             0x70
#define STRING_DATA              0x71
#define I2C_REQUEST              0x76
#define I2C_REPLY                0x77
#define I2C_CONFIG               0x78
#define REPORT_FIRMWARE          0x79
#define SAMPLING_INTERVAL        0x7A

// Pin modes
#define PIN_MODE_INPUT   0x00
#define PIN_MODE_OUTPUT  0x01
#define PIN_MODE_ANALOG  0x02
#define PIN_MODE_PWM     0x03
#define PIN_MODE_SERVO   0x04
#define PIN_MODE_I2C     0x06
#define PIN_MODE_PULLUP  0x0B

// I2C request modes (bits 3-4 of the mode byte)
#define I2C_WRITE        0x00
#define I2C_READ         0x08

#define FIRMATA_MAJOR    2
#define FIRMATA_MINOR    5

#define MAX_SYSEX        64

// ---- Serial backend --------------------------------------------------------
// Map these to your Pinguino board's serial API. Defaults assume USB CDC
// (PIC18F2550/4550 with USB). For a UART board, switch to Serial.* instead.
u8   fm_available()  { return CDC.available(); }
u8   fm_read()       { return CDC.read(); }
void fm_write(u8 b)  { CDC.write(b); }

// ---- State -----------------------------------------------------------------
u8  pinModes[TOTAL_PINS];
u16 pinValues[TOTAL_PINS];       // last output value (PWM/servo/digital)
u8  reportAnalog[TOTAL_ANALOG];
u8  reportDigital[TOTAL_PORTS];
u8  previousPort[TOTAL_PORTS];
u16 samplingInterval = 19;

u8  parseCommand = 0;
u8  parseChannel = 0;
u8  waitingBytes = 0;
u8  storedByte = 0;
u8  inSysex = 0;
u8  sysexBytes[MAX_SYSEX];
u8  sysexLength = 0;

u32 lastSample = 0;

// ---- Helpers ---------------------------------------------------------------
u8 isAnalogPin(u8 pin)  { return (pin >= ANALOG_BASE) && (pin < ANALOG_BASE + TOTAL_ANALOG); }
u8 isPwmPin(u8 pin)     { return (pin == 11) || (pin == 12); }   // CCP1 / CCP2 - adjust
u8 analogChannel(u8 pin){ return pin - ANALOG_BASE; }

// ---- Outgoing messages -----------------------------------------------------
void sendVersion()
{
    fm_write(REPORT_VERSION);
    fm_write(FIRMATA_MAJOR);
    fm_write(FIRMATA_MINOR);
}

void sendAnalog(u8 channel, u16 value)
{
    fm_write(ANALOG_MESSAGE | (channel & 0x0F));
    fm_write(value & 0x7F);
    fm_write((value >> 7) & 0x7F);
}

void sendDigitalPort(u8 port, u8 value)
{
    fm_write(DIGITAL_MESSAGE | (port & 0x0F));
    fm_write(value & 0x7F);
    fm_write((value >> 7) & 0x7F);
}

// Firmata sends each payload byte as a 7-bit LSB/MSB pair.
void sendString(const char *text)
{
    u8 i;
    fm_write(START_SYSEX);
    fm_write(STRING_DATA);
    for (i = 0; text[i] != 0; i++)
    {
        fm_write(text[i] & 0x7F);
        fm_write((text[i] >> 7) & 0x7F);
    }
    fm_write(END_SYSEX);
}

void sendFirmwareReport()
{
    const char *name = "PinguinoFirmata";
    u8 i;
    fm_write(START_SYSEX);
    fm_write(REPORT_FIRMWARE);
    fm_write(FIRMATA_MAJOR);
    fm_write(FIRMATA_MINOR);
    for (i = 0; name[i] != 0; i++)
    {
        fm_write(name[i] & 0x7F);
        fm_write((name[i] >> 7) & 0x7F);
    }
    fm_write(END_SYSEX);
}

void sendCapabilities()
{
    u8 pin;
    fm_write(START_SYSEX);
    fm_write(CAPABILITY_RESPONSE);
    for (pin = 0; pin < TOTAL_PINS; pin++)
    {
        fm_write(PIN_MODE_INPUT);  fm_write(1);
        fm_write(PIN_MODE_OUTPUT); fm_write(1);
        fm_write(PIN_MODE_PULLUP); fm_write(1);
        fm_write(PIN_MODE_SERVO);  fm_write(14);
        if (isAnalogPin(pin)) { fm_write(PIN_MODE_ANALOG); fm_write(10); }
        if (isPwmPin(pin))    { fm_write(PIN_MODE_PWM);    fm_write(8);  }
        fm_write(0x7F);        // end of this pin's modes
    }
    fm_write(END_SYSEX);
}

void sendAnalogMapping()
{
    u8 pin;
    fm_write(START_SYSEX);
    fm_write(ANALOG_MAPPING_RESPONSE);
    for (pin = 0; pin < TOTAL_PINS; pin++)
        fm_write(isAnalogPin(pin) ? analogChannel(pin) : 0x7F);
    fm_write(END_SYSEX);
}

void sendPinState(u8 pin)
{
    u16 value = (pin < TOTAL_PINS) ? pinValues[pin] : 0;
    fm_write(START_SYSEX);
    fm_write(PIN_STATE_RESPONSE);
    fm_write(pin);
    fm_write((pin < TOTAL_PINS) ? pinModes[pin] : PIN_MODE_INPUT);
    fm_write(value & 0x7F);
    if (value >> 7)   fm_write((value >> 7) & 0x7F);
    if (value >> 14)  fm_write((value >> 14) & 0x7F);
    fm_write(END_SYSEX);
}

// ---- Actuators -------------------------------------------------------------
void setPinMode(u8 pin, u8 mode)
{
    if (pin >= TOTAL_PINS)
        return;
    pinModes[pin] = mode;
    switch (mode)
    {
        case PIN_MODE_INPUT:
        case PIN_MODE_PULLUP: pinMode(pin, INPUT);  break;   // add pull-up if supported
        case PIN_MODE_OUTPUT:
        case PIN_MODE_PWM:    pinMode(pin, OUTPUT); break;
        case PIN_MODE_SERVO:  servo.attach(pin);    break;   // PINGUINO LIB: verify Servo API
        case PIN_MODE_ANALOG: /* analogRead selects the channel */ break;
    }
}

void writeAnalogPin(u8 pin, u16 value)
{
    if (pin >= TOTAL_PINS)
        return;
    pinValues[pin] = value;
    if (pinModes[pin] == PIN_MODE_SERVO)
        servo.write(pin, value);        // PINGUINO LIB: verify Servo API (angle 0-180)
    else
        analogWrite(pin, value & 0xFF); // PWM 0-255
}

void writePort(u8 port, u8 value)
{
    u8 i, pin;
    for (i = 0; i < 8; i++)
    {
        pin = port * 8 + i;
        if (pin < TOTAL_PINS && pinModes[pin] == PIN_MODE_OUTPUT)
        {
            pinValues[pin] = (value >> i) & 0x01;
            digitalWrite(pin, pinValues[pin]);
        }
    }
}

// ---- Sysex handlers --------------------------------------------------------
void handleServoConfig()   // payload: pin, minLSB, minMSB, maxLSB, maxMSB
{
    u8  pin = sysexBytes[1];
    u16 minPulse = sysexBytes[2] | (sysexBytes[3] << 7);
    u16 maxPulse = sysexBytes[4] | (sysexBytes[5] << 7);
    if (pin >= TOTAL_PINS)
        return;
    pinModes[pin] = PIN_MODE_SERVO;
    servo.attach(pin);                              // PINGUINO LIB
    servo.SetMinimumPulse(pin, minPulse);           // PINGUINO LIB
    servo.SetMaximumPulse(pin, maxPulse);           // PINGUINO LIB
}

void handleExtendedAnalog()  // payload: pin, valLSB, valMSB[, more]
{
    u8  pin = sysexBytes[1];
    u16 value = sysexBytes[2];
    if (sysexLength > 3) value |= (sysexBytes[3] << 7);
    writeAnalogPin(pin, value);
}

void handleSamplingInterval()  // payload: msLSB, msMSB
{
    samplingInterval = sysexBytes[1] | (sysexBytes[2] << 7);
    if (samplingInterval < 1)
        samplingInterval = 1;
}

// One-shot I2C write / read. PINGUINO LIB: adapt the I2C.* calls to your version.
void handleI2CRequest()
{
    u8  address = sysexBytes[1];
    u8  mode    = sysexBytes[2] & 0x18;
    u8  i;

    if (mode == I2C_WRITE)
    {
        I2C.start();
        I2C.write(address << 1);                    // write address
        for (i = 3; i + 1 < sysexLength; i += 2)
            I2C.write(sysexBytes[i] | (sysexBytes[i + 1] << 7));
        I2C.stop();
    }
    else if (mode == I2C_READ)
    {
        // payload: addr, mode, [regLSB, regMSB,] countLSB, countMSB
        u8  hasReg = (sysexLength >= 7);
        u8  reg    = hasReg ? (sysexBytes[3] | (sysexBytes[4] << 7)) : 0;
        u8  ci     = hasReg ? 5 : 3;
        u8  count  = sysexBytes[ci] | (sysexBytes[ci + 1] << 7);
        u8  b;

        if (hasReg)
        {
            I2C.start();
            I2C.write(address << 1);
            I2C.write(reg);
            I2C.stop();
        }
        I2C.start();
        I2C.write((address << 1) | 1);              // read address
        fm_write(START_SYSEX);
        fm_write(I2C_REPLY);
        fm_write(address & 0x7F); fm_write((address >> 7) & 0x7F);
        fm_write(reg & 0x7F);     fm_write((reg >> 7) & 0x7F);
        for (i = 0; i < count; i++)
        {
            b = I2C.read(i < count - 1);            // ack until the last byte
            fm_write(b & 0x7F);
            fm_write((b >> 7) & 0x7F);
        }
        I2C.stop();
        fm_write(END_SYSEX);
    }
}

void handleSysex()
{
    switch (sysexBytes[0])
    {
        case REPORT_FIRMWARE:      sendFirmwareReport();     break;
        case CAPABILITY_QUERY:     sendCapabilities();       break;
        case ANALOG_MAPPING_QUERY: sendAnalogMapping();      break;
        case PIN_STATE_QUERY:      sendPinState(sysexBytes[1]); break;
        case SERVO_CONFIG:         handleServoConfig();      break;
        case EXTENDED_ANALOG:      handleExtendedAnalog();   break;
        case SAMPLING_INTERVAL:    handleSamplingInterval(); break;
        case I2C_CONFIG:           /* I2C.master(); */       break;  // PINGUINO LIB: init I2C
        case I2C_REQUEST:          handleI2CRequest();       break;
        // STRING_DATA / SERIAL_MESSAGE inbound are accepted but not acted on.
    }
}

void systemReset()
{
    u8 i;
    for (i = 0; i < TOTAL_PINS; i++)  { pinModes[i] = PIN_MODE_OUTPUT; pinValues[i] = 0; }
    for (i = 0; i < TOTAL_ANALOG; i++) reportAnalog[i] = 0;
    for (i = 0; i < TOTAL_PORTS; i++)  { reportDigital[i] = 0; previousPort[i] = 0; }
    samplingInterval = 19;
}

// ---- Two/one data-byte commands --------------------------------------------
void handleTwoBytes(u8 command, u8 channel, u8 b1, u8 b2)
{
    u16 value = b1 | (b2 << 7);
    switch (command)
    {
        case ANALOG_MESSAGE:         writeAnalogPin(channel, value);  break;
        case DIGITAL_MESSAGE:        writePort(channel, value);       break;
        case SET_PIN_MODE:           setPinMode(b1, b2);              break;
        case SET_DIGITAL_PIN_VALUE:
            if (b1 < TOTAL_PINS) { pinValues[b1] = b2 & 0x01; digitalWrite(b1, b2 & 0x01); }
            break;
    }
}

void handleOneByte(u8 command, u8 channel, u8 b1)
{
    if (command == REPORT_ANALOG && channel < TOTAL_ANALOG)
        reportAnalog[channel] = b1 & 0x01;
    else if (command == REPORT_DIGITAL && channel < TOTAL_PORTS)
        reportDigital[channel] = b1 & 0x01;
}

// ---- Byte parser -----------------------------------------------------------
void processByte(u8 b)
{
    if (inSysex)
    {
        if (b == END_SYSEX)
        {
            inSysex = 0;
            if (sysexLength > 0)
                handleSysex();
        }
        else if (sysexLength < MAX_SYSEX)
        {
            sysexBytes[sysexLength++] = b;
        }
        return;
    }

    if (b >= 0x80)               // command byte
    {
        u8 command = b & 0xF0;
        if (command == DIGITAL_MESSAGE || command == ANALOG_MESSAGE)
        {
            parseCommand = command; parseChannel = b & 0x0F; waitingBytes = 2;
        }
        else if (command == REPORT_ANALOG || command == REPORT_DIGITAL)
        {
            parseCommand = command; parseChannel = b & 0x0F; waitingBytes = 1;
        }
        else if (b == SET_PIN_MODE || b == SET_DIGITAL_PIN_VALUE)
        {
            parseCommand = b; parseChannel = 0; waitingBytes = 2;
        }
        else if (b == START_SYSEX)
        {
            inSysex = 1; sysexLength = 0;
        }
        else if (b == REPORT_VERSION) { sendVersion();  waitingBytes = 0; }
        else if (b == SYSTEM_RESET)   { systemReset();  waitingBytes = 0; }
        else                          { waitingBytes = 0; }
        return;
    }

    if (waitingBytes == 2)
    {
        storedByte = b; waitingBytes = 1;
    }
    else if (waitingBytes == 1)
    {
        waitingBytes = 0;
        if (parseCommand == REPORT_ANALOG || parseCommand == REPORT_DIGITAL)
            handleOneByte(parseCommand, parseChannel, b);
        else
            handleTwoBytes(parseCommand, parseChannel, storedByte, b);
    }
}

// ---- Reporting -------------------------------------------------------------
void reportInputs()
{
    u8 port, channel, i, pin, value;

    for (channel = 0; channel < TOTAL_ANALOG; channel++)
        if (reportAnalog[channel])
            sendAnalog(channel, analogRead(channel));

    for (port = 0; port < TOTAL_PORTS; port++)
    {
        if (!reportDigital[port])
            continue;
        value = 0;
        for (i = 0; i < 8; i++)
        {
            pin = port * 8 + i;
            if (pin < TOTAL_PINS && pinModes[pin] != PIN_MODE_OUTPUT && digitalRead(pin))
                value |= (1 << i);
        }
        if (value != previousPort[port])
        {
            previousPort[port] = value;
            sendDigitalPort(port, value);
        }
    }
}

// ---- Entry points ----------------------------------------------------------
void setup()
{
    systemReset();
    sendVersion();
    sendFirmwareReport();
}

void loop()
{
    while (fm_available())
        processByte(fm_read());

    if ((u32)(millis() - lastSample) >= samplingInterval)
    {
        lastSample = millis();
        reportInputs();
    }
}
