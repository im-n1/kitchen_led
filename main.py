# import network
import uasyncio
import ujson
from machine import PWM, Pin

from mqtt_as import MQTTClient
from mqtt_as import config as mqtt_config

DEBUG = True

WIFI_SSID = "n1.home.slow"
WIFI_PASSWORD = "polibmiprdel"

MQTT_HOST = "o2.home"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_IN = "home/kitchen/bottom_led/in"
MQTT_TOPIC_OUT = "home/kitchen/bottom_led/out"
MQTT_TOPIC_LOG = "home/kitchen/bottom_led/logs"
MQTT_TOPIC_OFFLINE = "home/kitchen/bottom_led/offline"
MQTT_OFFLINE_MESSAGE = "0"
MQTT_RETAIN = True
MQTT_QOS = 1

# Limits
MAX_DUTY = 1023
MAX_FREQUENCY = 1000

# TODO: zjistit. k cemu se realne pouziva a pripadne prejmenovat
KEEPALIVE = 10

R_PIN = 14  # D5 on the board
G_PIN = 12  # D6 on the board
B_PIN = 13  # D7 on the board


def log(message):
    """
    Logs a message to /log file.
    Debugging is for development purposes only. It causes chip
    slowdown as the chip opens/writes/closes the file multiple
    times you can notice delays in operations.

    :param str message: A message to log.
    """

    # with open("log", "a") as f:
    #     f.write(f"{message}\n")


class Mqtt:
    """
    Represents MQTT as a whole inc. config.
    """

    def __init__(self, machine):
        """
        Constructor.

        :param Machine machine: Machine class instance (used mainly in on_* callbacks)
        """

        config = mqtt_config
        config["connect_coro"] = self.on_connect
        config["subs_cb"] = self.on_message
        config["server"] = MQTT_HOST
        config["user"] = MQTT_USER
        config["password"] = MQTT_PASSWORD
        config["ssid"] = WIFI_SSID
        config["wifi_pw"] = WIFI_PASSWORD
        config["keepalive"] = KEEPALIVE
        config["will"] = [
            MQTT_TOPIC_OFFLINE,  # cannot be same as MQTT_TOPIC
            MQTT_OFFLINE_MESSAGE,
            MQTT_RETAIN,
            MQTT_QOS,
        ]
        MQTTClient.DEBUG = DEBUG
        self.client = MQTTClient(config)
        self.machine = machine
        self.led_strip = LEDStrip(machine)

    async def on_connect(self, client):
        """
        Is spawned when MQTT establishes a connection.

        :param MQTTClient client: MQTT client instance.
        """

        await client.subscribe(MQTT_TOPIC_IN, MQTT_QOS)
        await self.publish_strip_state()

    def on_message(self, topic, message, retained):
        """
        {
            "device": ...,
            "data": ...,
        }
        """

        log(f"A MQTT message received: {topic} -> {message}")

        try:
            data = ujson.loads(message.decode("utf-8"))
        except:
            log(f"Cannot parse incomming message as JSON: {message}")

        log("Message parsed!")

        self.led_strip.process_message(data)

    def __getattr__(self, key):
        """
        Ensures that every property/method is redirected
        to MQTT client.
        """

        return getattr(self.client, key)

    async def publish_led_strip_state(self):
        """
        Publishes current led strip state to MQTT as JSON.
        """

        await self.client.publish(
            MQTT_TOPIC_OUT,
            ujson.dumps(
                {
                    "device": self.led_strip.name,
                    "data": self.led_strip.get_current_state(),
                }
            ),
            retain=True,
        )


class LEDStrip:

    name = "led_strip"

    def __init__(self, machine):

        self.machine = machine
        self.red_pin = PWM(Pin(R_PIN), freq=1000)
        self.green_pin = PWM(Pin(G_PIN), freq=1000)
        self.blue_pin = PWM(Pin(B_PIN), freq=1000)
        self.red = 0
        self.green = 0
        self.blue = 0
        self.brightness = 255

    def perc_to_duty(self, percs):
        """
        Converts percentage to duty value where:
        0% -> 0 duty
        100% -> MAX_DUTY

        :param int percs: Percentage value.
        :return: Calculated PWM duty value.
        :rtype: int
        """

        return int(percs / 100 * MAX_DUTY)

    def value_to_duty(self, value):

        if 0 == value:
            to_return = 0
        else:
            to_return = int(value / 255 * MAX_DUTY)

        log(f"Duty calculated to {to_return}")

        return to_return

    def to_percents(self, value):
        """
        Converts 0 - 255 values to 0 - 100 scale (percents).

        :param int value: 0 - 255 value.
        :return: Percentages.
        :rtype: int
        """

        return int(value / (255 / 100))

    def to_red(self, value):
        """
        Sets red color brightness.

        :param int value: Brightness in RGB value 0 - 255.
        """

        self.red = value
        red = int(value * (self.to_percents(self.brightness) / 100))
        self.red_pin.duty(self.value_to_duty(red))
        log(f"Red is {red}")

    def to_green(self, value):
        """
        Sets green color brightness.

        :param int value: Brightness in RGB value 0 - 255.
        """

        self.green = value
        green = int(value * (self.to_percents(self.brightness) / 100))
        self.green_pin.duty(self.value_to_duty(green))
        log(f"Green is {green}")

    def to_blue(self, value):
        """
        Sets blue color brightness.

        :param int value: Brightness in RGB value 0 - 255.
        """

        self.blue = value
        blue = int(value * (self.to_percents(self.brightness) / 100))
        self.blue_pin.duty(self.value_to_duty(blue))
        log(f"Blue is {blue}")

    def white(self, value):
        """
        Sets led strip to white color or turns it off.

        :param bool value: Flag for white/off.
        """

        log(f"Settings white brightness to {value}")
        self.to_red(value)
        self.to_green(value)
        self.to_blue(value)
        log(f"White is {value}")

    def set_brightness(self, value):
        """
        Sets brightness of all colors.

        :param int brightness: 0 - 255 brightness value.
        """

        log(
            f"Settings RGB brightness with brightness {value} and r: {self.red} g: {self.green} b: {self.blue}"
        )
        self.brightness = value
        self.to_red(self.red)
        self.to_green(self.green)
        self.to_blue(self.blue)

    # def set_frequency(self, value):
    #     """
    #     Set's frequency (blinking) for all colors
    #     at once.
    #
    #     :param int value: Frequency in Hz for all 3 colors.
    #     """
    #
    #     value = min(int(value), MAX_FREQUENCY)
    #     self.red.freq(value)
    #     self.green.freq(value)
    #     self.blue.freq(value)
    #     self.machine.log(f"Frequency is {value}")

    def get_current_state(self):
        """
        Returns current light state.
        """
        return {
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "brightness": self.brightness,
        }

    def process_message(self, data):
        """
        Processes messages from HomeAssistant. Those messages have following structure:

        {
          "brightness": 255,
          "color_mode": "rgb",
          "color_temp": 155,
          "color": {
            "r": 255,
            "g": 180,
            "b": 200,
            "c": 100,
            "w": 50,
            "x": 0.406,
            "y": 0.301,
            "h": 344.0,
            "s": 29.412
          },
          "effect": "colorloop",
          "state": "ON",
          "transition": 2,
        }

        Following use-case messages are processed:

        Turn on - {"state":"ON"}
        Turn off - {"state":"OFF"}
        Set RGB value - {"state":"ON","color":{"r":255,"g":64,"b":255}}
        Set RGB brightness - {"state":"ON","brightness":40}
        Set white brightness - {"state":"ON","white":189}
        """

        log("Processing message")

        # Set RGB value.
        if "ON" == data["state"] and "color" in data:
            log("Setting RGB")
            self.to_red(data["color"]["r"])
            self.to_green(data["color"]["g"])
            self.to_blue(data["color"]["b"])

        # Set RGB brightness.
        elif "ON" == data["state"] and "brightness" in data:
            self.set_brightness(data["brightness"])

        # Set white brightness.
        elif "ON" == data["state"] and "white" in data:
            self.white(data["white"])

        # Set white brightness.
        elif "ON" == data["state"]:
            log("Turning on")
            self.white(255)

        # Set white brightness.
        elif "OFF" == data["state"]:
            log("Turning off")
            self.white(0)

        log("Message processed")

        # if "f" in data:
        #     self.set_frequency(data["f"])


class Machine:
    """
    Main class to operate with.
    Represents the board.
    """

    def __init__(self):

        self.logs = []
        open("log", "w").close()

    def run(self):

        try:
            uasyncio.run(self.start())
        finally:
            self.mqtt.close()

    def log(self, message):

        self.logs.append(message)

    async def start(self):
        """
        Starts following async tasks:
        - mqtt client
        """

        loop = uasyncio.get_event_loop()
        loop.create_task(self.mqtt_task())
        await loop.run_forever()

    async def mqtt_task(self):
        """
        Handles MQTT connection. If no connection cannot be
        established retries again in 15 seconds.
        """

        while True:

            try:
                log("Connecting to MQTT...")

                self.mqtt = Mqtt(self)
                await self.mqtt.connect()
                # await self.mqtt.publish("home/kitchen/led", "ahoj", retain=True)

                log("Connected to MQTT!")

                while True:
                    await self.flush_logs()
                    await uasyncio.sleep(3)

            except Exception as e:
                log(type(e))
                log(e)
                # log(e.__traceback__)

                log("Couldn't connect to MQTT ... reconnecting")
                await uasyncio.sleep(15)

    async def flush_logs(self):

        while self.logs:
            try:
                message = self.logs.pop()
            except IndexError:
                break

            await self.mqtt.publish(MQTT_TOPIC_LOG, message, retain=True)


m = Machine()
m.run()
