#include <Arduino.h>

// --- CONFIGURATION ---
const int SIGNAL_PIN = 8;

// --- FAST GPIO MACROS (AVR Specific) ---
#if defined(ARDUINO_ARCH_AVR)
    #define SIGNAL_PORT PORTB
    #define SIGNAL_DDR  DDRB
    #define SIGNAL_BIT  0

    #define FAST_SETUP() (SIGNAL_DDR |= (1 << SIGNAL_BIT))
    #define FAST_HIGH()  (SIGNAL_PORT |= (1 << SIGNAL_BIT))
    #define FAST_LOW()   (SIGNAL_PORT &= ~(1 << SIGNAL_BIT))
    #define FAST_TOGGLE() (PINB = (1 << SIGNAL_BIT))

// --- FALLBACK (STM32, generic, etc) ---
#else
    #define FAST_SETUP() pinMode(SIGNAL_PIN, OUTPUT)
    #define FAST_HIGH()  digitalWrite(SIGNAL_PIN, HIGH)
    #define FAST_LOW()   digitalWrite(SIGNAL_PIN, LOW)
    #define FAST_TOGGLE() digitalWrite(SIGNAL_PIN, !digitalRead(SIGNAL_PIN))
#endif

// --- C-COMPATIBLE BRIDGE ---
extern "C" {
    void signal_setup() { FAST_SETUP(); }
    void signal_high() { FAST_HIGH(); }
    void signal_low() { FAST_LOW(); }
    void signal_pulse() {
        FAST_HIGH();
        FAST_LOW(); 
    }

}
