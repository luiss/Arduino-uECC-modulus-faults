#include <Arduino.h>
#include <uECC.h>
#include <types.h>

// --- Serial input size ---
#define HASH_SIZE 32
#define SIGNATURE_SIZE 64
#define PRIV_SIZE 32
#define PUB_SIZE 65  

void printBytesAsHex(uint8_t* buffer, size_t length);

// printf function to be used inside uECC
extern "C" void c_logln(const char* message) {
    Serial.println(message);
}

extern "C" void c_log(const char* message) {
    Serial.print(message);
}

extern "C" void c_log_hex(uint8_t* buffer, size_t length) {
  printBytesAsHex(buffer, length);
}

// Trigger
extern "C" void signal_setup();

// **************************************************
// *********** Function Prototypes ******************
// **************************************************

void waitForInputBytes();
int tmp_cnt = 0;

// Local key structure
struct ECCKey {
  struct uECC_Curve_t * curve;
  uint8_t privkey[PRIV_SIZE];
  uint8_t pubkey[PUB_SIZE];
};

ECCKey keys;

// static int RNG(uint8_t *dest, unsigned size) {
//   // Use the least-significant bits from the ADC for an unconnected pin (or connected to a source of 
//   // random noise). This can take a long time to generate random data if the result of analogRead(0) 
//   // doesn't change very frequently.
//   while (size) {
//     uint8_t val = 0;
//     for (unsigned i = 0; i < 8; ++i) {
//       int init = analogRead(0);
//       int count = 0;
//       while (analogRead(0) == init) {
//         ++count;
//       }
      
//       if (count == 0) {
//          val = (val << 1) | (init & 0x01);
//       } else {
//          val = (val << 1) | (count & 0x01);
//       }
//     }
//     *dest = val;
//     ++dest;
//     --size;
//   }
//   return 1;
// }

// WARNING !!!!!!!! --- FIXED RNG -- WARNING !!!!!! -- To use onl for the Fault attack
static int RNG(uint8_t *dest, unsigned size) {
  // Instead of reading ADC, fill the buffer with a fixed pattern
  for (unsigned i = 0; i < size; ++i) {
    dest[i] = i;
  }
  return 1;
}

// print an Hex array
void printBytesAsHex(uint8_t* buffer, size_t length) {
  for (size_t i = 0; i < length; i++) {
    if (buffer[i] < 0x10) {
      Serial.print("0");
    }
    Serial.print(buffer[i], HEX);
  }
  Serial.println();
}

ECCKey keygen() {
  ECCKey keys;
  keys.curve = uECC_secp256r1();
  
  uECC_make_key(keys.pubkey, keys.privkey, keys.curve);
  
  return keys;
}

void ecdsa_sign(ECCKey keys, const uint8_t *hash_m, uint8_t * signature){

  uECC_sign(keys.privkey, hash_m, HASH_SIZE, signature, keys.curve);

  Serial.print("Signature: ");
  printBytesAsHex(signature, SIGNATURE_SIZE);
}

void test_ecdsa(uint8_t *hash_m){
  uint8_t signature[SIGNATURE_SIZE];
  ecdsa_sign(keys, hash_m, signature);
}

void waitForInputBytes() {
  while (Serial.available() < HASH_SIZE) {
  }
  uint8_t buffer[HASH_SIZE];
  
  Serial.readBytes(buffer, HASH_SIZE);

  test_ecdsa(buffer);
}

// ******************* //
// ***** Setup ******* //
// ****************** //
void setup() {
  Serial.begin(500000);

  uECC_set_rng(&RNG);
  
  signal_setup(); // Sets trigger Pin OUTPUT

  keys = keygen();
  Serial.println();
  Serial.print("Priv Key: "); printBytesAsHex(keys.privkey, PRIV_SIZE);
  Serial.print("Pub  Key: "); printBytesAsHex(keys.pubkey, PUB_SIZE);
}

void loop() {

  waitForInputBytes();
  
}