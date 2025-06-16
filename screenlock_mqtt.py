#!/usr/bin/env python3

import os
import sys
import signal
import logging
import json
from datetime import datetime
from Foundation import NSDistributedNotificationCenter, NSNotificationCenter, NSRunLoop, NSDate
from AppKit import NSWorkspace, NSWorkspaceWillPowerOffNotification
import paho.mqtt.client as mqtt

class ScreenLockMQTTReporter:
    def __init__(self, mqtt_broker, mqtt_port=1883, mqtt_topic="macos/screenlock", 
                 mqtt_username=None, mqtt_password=None):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if mqtt_username and mqtt_password:
            self.mqtt_client.username_pw_set(mqtt_username, mqtt_password)
        
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        
        self.running = True
        self.setup_logging()
        self.setup_signal_handlers()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, exiting gracefully")
        self.running = False
    
    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.logger.info("Connected to MQTT broker")
        else:
            self.logger.error(f"Failed to connect to MQTT broker: {reason_code}")
    
    def on_mqtt_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self.logger.info("Disconnected from MQTT broker")
    
    def publish_state(self, is_locked):
        payload = "true" if is_locked else "false"
        
        try:
            result = self.mqtt_client.publish(self.mqtt_topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Published state: {payload}")
            else:
                self.logger.error(f"Failed to publish state: {result.rc}")
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
    
    def screen_lock_notification_(self, notification):
        self.logger.info("Screen locked")
        self.publish_state(True)
    
    def screen_unlock_notification_(self, notification):
        self.logger.info("Screen unlocked")
        self.publish_state(False)
    
    def power_off_notification_(self, notification):
        self.logger.info("System shutting down")
        self.publish_state(True)
    
    def start(self):
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Register for screen lock/unlock notifications
            nc = NSDistributedNotificationCenter.defaultCenter()
            nc.addObserver_selector_name_object_(
                self, 'screen_lock_notification:', 
                'com.apple.screenIsLocked', None
            )
            nc.addObserver_selector_name_object_(
                self, 'screen_unlock_notification:', 
                'com.apple.screenIsUnlocked', None
            )
            
            # Register for power off notifications
            workspace_nc = NSWorkspace.sharedWorkspace().notificationCenter()
            workspace_nc.addObserver_selector_name_object_(
                self, 'power_off_notification:',
                NSWorkspaceWillPowerOffNotification, None
            )
            
            self.logger.info("Started monitoring screen lock/unlock events")
            self.publish_state(False)
            
            # Start the run loop with periodic checks
            run_loop = NSRunLoop.currentRunLoop()
            while self.running:
                run_loop.runMode_beforeDate_('NSDefaultRunLoopMode', NSDate.dateWithTimeIntervalSinceNow_(1.0))
            
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.logger.info("Exited gracefully")
            
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            sys.exit(1)

def main():
    # Configuration - can be set via environment variables
    mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
    mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
    mqtt_topic = os.getenv('MQTT_TOPIC', 'macos/screenlock')
    mqtt_username = os.getenv('MQTT_USERNAME')
    mqtt_password = os.getenv('MQTT_PASSWORD')
    
    if not mqtt_broker:
        print("Error: MQTT_BROKER environment variable is required")
        sys.exit(1)
    
    reporter = ScreenLockMQTTReporter(
        mqtt_broker=mqtt_broker,
        mqtt_port=mqtt_port,
        mqtt_topic=mqtt_topic,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password
    )
    
    reporter.start()

if __name__ == "__main__":
    main()