import wifi
import socketpool
import ssl
import adafruit_requests
import time
import microcontroller
import json
import os
import board
import busio
from adafruit_ens160 import ENS160
from adafruit_ahtx0 import AHTx0

class TelegramBot:
    def __init__(self):
        self.token = '[TELEGRAMBOTTOKEN}'
        self.default_chat_id = '{CHAT_ID}'
        self.api_url = "https://api.telegram.org/bot{}/sendMessage"
        self.get_url = "https://api.telegram.org/bot{}/getUpdates"
        
        self.pi_ip = "DATABASE"
        self.api_endpoint = f"API_ENDPOINT"
        
        self.setup_network()
        
        pool = socketpool.SocketPool(wifi.radio)
        self.requests = adafruit_requests.Session(pool, ssl.create_default_context())
        
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ens160 = ENS160(self.i2c)
        self.aht = AHTx0(self.i2c)

    def setup_network(self):
        print("Connecting to WiFi...")
        try:
            wifi.radio.connect(
                os.getenv('WIFI_SSID'),
                os.getenv('WIFI_PASSWORD')
            )
            print("Connected to", os.getenv('WIFI_SSID'))
            print("IP:", wifi.radio.ipv4_address)
        except Exception as e:
            print("Failed to connect to WiFi:", e)

    def send_message(self, message, chat_id=None):
        if chat_id is None:
            chat_id = self.default_chat_id
            
        data = {
            "chat_id": chat_id,
            "text": message
        }
        
        try:
            response = self.requests.post(
                self.api_url.format(self.token),
                json=data
            )
            print("Message sent:", message)
            response.close()
            return True
        except Exception as e:
            print("Failed to send message:", e)
            return False

    def send_sensor_data_to_pi(self, humidity, temperature, eco2, tvoc, aqi):
        try:
            data = {
                "humidity": humidity,
                "temperature": temperature,
                "eCO2": eco2,
                "TVOC": tvoc,
                "AQI": aqi
            }
            
            response = self.requests.post(
                self.api_endpoint,
                json=data
            )
            print("Data sent to Pi:", response.json())
            response.close()
            return True
            
        except Exception as e:
            print(f"Failed to send data to Pi: {e}")
            return False

    def get_sensor_data(self):
        try:
            # Read sensor data
            temperature = self.aht.temperature
            humidity = self.aht.relative_humidity
            eco2 = self.ens160.eCO2
            tvoc = self.ens160.TVOC
            aqi = self.ens160.AQI
            # Send to Raspberry Pi
            self.send_sensor_data_to_pi(humidity, temperature, eco2, tvoc, aqi)
            
            message = (
                f"Temperature: {temperature:.1f}°C\n" +
                f"Humidity: {humidity:.1f}%\n" +
                f"eCO2: {eco2} ppm\n" +
                f"TVOC: {tvoc} ppb\n" +
                f"Air Quality Index: {aqi}"
            )
            
            return message
        except Exception as e:
            return f"Error reading/sending sensor data: {str(e)}"
def main():
    bot = TelegramBot()
    bot.send_message("Sensor monitoring started!")
    
    # Main loop
    while True:
        try:
            sensor_data = bot.get_sensor_data()
            bot.send_message(sensor_data)
          
            time.sleep(30)
            
        except Exception as e:
            print("Error in main loop:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
