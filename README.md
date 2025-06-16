# macOS Screen Lock MQTT Reporter

A Python program that reports macOS screen lock/unlock events and system shutdown to an MQTT broker.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set these environment variables:

- `MQTT_BROKER` (required): MQTT broker hostname/IP
- `MQTT_PORT` (optional): MQTT broker port (default: 1883)
- `MQTT_TOPIC` (optional): MQTT topic (default: "macos/screenlock")
- `MQTT_USERNAME` (optional): MQTT username
- `MQTT_PASSWORD` (optional): MQTT password

## Usage

```bash
export MQTT_BROKER=your-mqtt-broker.my-tailnet.ts.net
python3 screenlock_mqtt.py
```

## Running as a Service

See `com.user.screenlock-mqtt.plist` for a launchd plist example. Update the paths and environment variables as needed, then install it:

```bash
cp com.user.screenlock-mqtt.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.screenlock-mqtt.plist
```

# License

MIT; see [LICENSE] in this repo.

# Author

Chris Dzombak
- [github.com/cdzombak](https://www.github.com/cdzombak)
- [dzombak.com](https://www.dzombak.com)
