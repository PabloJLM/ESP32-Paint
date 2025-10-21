#include <TFT_eSPI.h>
#include <SPI.h>

TFT_eSPI tft = TFT_eSPI();

bool receivingImage = false;
int x = 0, y = 0;

uint16_t htmlToColor(String html) {
  if (html.length() != 7 || html[0] != '#') return TFT_BLACK;
  long r = strtol(html.substring(1, 3).c_str(), NULL, 16);
  long g = strtol(html.substring(3, 5).c_str(), NULL, 16);
  long b = strtol(html.substring(5, 7).c_str(), NULL, 16);
  return tft.color565(r, g, b);
}


void setup() {
  Serial.begin(115200);//probar con mas xd
  tft.init();
  tft.setRotation(3);
  tft.fillScreen(TFT_WHITE);
  tft.setTextColor(TFT_BLACK, TFT_WHITE);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("Paint ESP32", 120, 67, 2);
  tft.drawString("Por: PJLM", 120, 90, 2);
}

void loop() {
  if (Serial.available()) {
    if (receivingImage) {
      while (Serial.available() >= 2) {
        uint16_t color = (Serial.read() << 8) | Serial.read();
        tft.drawPixel(x, y, color);
        x++;
        if (x >= 240) { x = 0; y++; }//cambiar por resulucion real
        if (y >= 135) { receivingImage = false; break; }
      }
      return;
    }

    String data = Serial.readStringUntil('\n');
    data.trim();

    if (data == "CLEAR") {
      tft.fillScreen(TFT_WHITE);
      return;
    }

    if (data == "WHITE") {
      tft.fillScreen(TFT_WHITE);
      return;
    }

    if (data == "BLACK") {
      tft.fillScreen(TFT_BLACK);
      return;
    }

    if (data == "IMG_START") {
      receivingImage = true;
      x = 0; y = 0;
      tft.startWrite();
      return;
    }

    if (data == "IMG_END") {
      receivingImage = false;
      tft.endWrite();
      return;
    }
    int c1 = data.indexOf(',');
    int c2 = data.indexOf(',', c1 + 1);
    int c3 = data.indexOf(',', c2 + 1);

    if (c1 < 0 || c2 < 0 || c3 < 0) return;

    int x = data.substring(0, c1).toInt();
    int y = data.substring(c1 + 1, c2).toInt();
    String htmlColor = data.substring(c2 + 1, c3);
    int size = data.substring(c3 + 1).toInt();

    uint16_t color = htmlToColor(htmlColor);

    tft.fillCircle(x, y, size, color);
  }
}
