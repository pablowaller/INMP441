#include <driver/i2s.h>

#define I2S_WS  25  // Word select (L/R CLK)
#define I2S_SD  33  // Serial data
#define I2S_SCK 26  // Serial clock (BCLK)

void setup() {
  Serial.begin(115200);

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S_MSB,
    .intr_alloc_flags = 0,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

void loop() {
  int32_t buffer[64];
  size_t bytes_read;

  i2s_read(I2S_NUM_0, &buffer, sizeof(buffer), &bytes_read, portMAX_DELAY);

  int64_t sum = 0;
  int32_t max_sample = 0;

  for (int i = 0; i < 64; i++) {
    int32_t sample = buffer[i] >> 14; 
    sum += abs(sample);
    if (abs(sample) > max_sample) max_sample = abs(sample);
  }

  float avg = sum / 64.0;

  Serial.printf("Avg: %.2f | Max: %d\n", avg, max_sample);

  delay(100); 
}
