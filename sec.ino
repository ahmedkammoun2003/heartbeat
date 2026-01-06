#include <ASCON.h>


uint8_t key[16]   = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};
uint8_t nonce[16] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};

void setup() {
  Serial.begin(115200);
  pinMode(34, INPUT);
  delay(1000);
  Serial.println("--- ASCON-128 SECURE READY ---");
}

void loop() {
  int sensorValue = analogRead(34);
  String plaintext = "HR:" + String(sensorValue);
  
  size_t len = plaintext.length();
  uint8_t ciphertext[len + 16]; 
  size_t ciphertext_len;

  // Encryption Function Signature for this library:
  // ascon128_aead_encrypt(out_cipher, out_len, plain, plain_len, assoc, assoc_len, nonce, key)
  ascon128_aead_encrypt(
    ciphertext, &ciphertext_len, 
    (const uint8_t*)plaintext.c_str(), len, 
    NULL, 0, 
    nonce, key
  );

  // Print Results
  Serial.print("Data: "); Serial.print(plaintext);
  Serial.print(" | Encrypted Hex: ");
  
  // The output includes the ciphertext AND the tag appended at the end
  for (size_t i = 0; i < ciphertext_len; i++) {
    if (ciphertext[i] < 0x10) Serial.print("0");
    Serial.print(ciphertext[i], HEX);
  }
  
  Serial.println();
  delay(20);
} 