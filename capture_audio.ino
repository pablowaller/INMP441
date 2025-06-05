#include <driver/i2s.h>

#define I2S_WS 25
#define I2S_SD 33
#define I2S_SCK 26
#define SAMPLE_RATE 16000
#define RECORD_SECONDS 3
#define DISCARD_MS 200  

#define SAMPLES_TO_DISCARD (SAMPLE_RATE * DISCARD_MS / 1000)
#define TOTAL_SAMPLES (SAMPLE_RATE * RECORD_SECONDS)

int16_t samples[TOTAL_SAMPLES];

void setupI2S() {
  const i2s_config_t i2s_config = {
    .mode = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = 1024,
    .use_apll = false
  };

  const i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_zero_dma_buffer(I2S_NUM_0);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  setupI2S();

  Serial.println("Grabando...");

  int16_t basura[SAMPLES_TO_DISCARD];
  size_t bytesRead;
  i2s_read(I2S_NUM_0, (void*)basura, sizeof(basura), &bytesRead, portMAX_DELAY);

  i2s_read(I2S_NUM_0, (void*)samples, sizeof(samples), &bytesRead, portMAX_DELAY);

  Serial.println("Grabacion completa");

  for (int i = 0; i < TOTAL_SAMPLES; i++) {
    Serial.write((uint8_t*)&samples[i], sizeof(int16_t));
  }

  Serial.println("Fin de la transmision.");
}

void loop() {}
