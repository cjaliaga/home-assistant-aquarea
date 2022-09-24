# Manage Panasonic Aquarea Smart Cloud devices from Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub Release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/cjaliaga/home-assistant-aquarea?include_prereleases)

Panasonic Aquarea Smart Cloud is a cloud service that allows you to control your Panasonic Aquarea heat pump from your smartphone. This integration allows you to control your heat pump from Home Assistant.

The integration uses [aioaquarea](https://github.com/cjaliaga/aioaquarea) to communicate with the Panasonic Aquarea Smart Cloud service.

This integration is currently in beta. Please report any issues you find and any feedback you may have. Thanks!

**⚠️ Make sure to read the 'Remarks' and 'Warning' sections**

## Features
* Climate entity per device zone that allows you to control the operation mode, read the current temperature of the water in the device/zone and (if the zone supports it), change the target temperature.
* Sensor entity for the outdoor temperature.
* Water heater entity for the hot water tank (if the device has one), that allows you to control the operation mode (enabled/disabled) and read the current temperature of the water in the tank.
* Diagnostic sensor to indicate if the device has any problem (such not enough water flow).

## Features in the works
* Consumption sensors.
* Weekly schedule.
* Set the device in eco mode/quiet mode/holiday mode (if the device supports it).
* Set the device in away mode (if the device supports it).
* Additional sensors/switches for the device.

## ⚠️ Update to v0.2.0 from v0.1.X
If you are updating from a version prior to v0.2.0, the recommendation is for you to remove the integration and add it again before updating. This is because v0.2.0 introduces a breaking change in the unique id generation for the entities. If you don't remove the integration and add it again, you will end up with duplicate entities.

This is a one time thing during the beta that was needed in order to support multiple devices and zones. From now on, the unique id generation will be stable and you won't need to remove the integration and add it again.

## Remarks
Panasonic only allows one connection per account at the same time. This means that if you open the session from the Panasonic Confort Cloud app or the Panasonic Confort Cloud website, the session will be closed and you will be disconnected from Home Assistant. The integration will try to reconnect automatically, clossing the session from the app or the website. If you want to use the app or the website, you will have to temporarily disable the integration.

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

1. Download the integration via (one of them):
   - [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cjaliaga&repository=home-assistant-aquarea&category=integration)
   - Go to HACS > Integrations > Look for "Aquarea" 

2. Restart Home Assistant
3. Add integration via (one of them):
   - [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aquarea)
   - Go to "Settings" >> "Devices & Services", click "+ ADD INTEGRATION" and select "Aquarea Smart Cloud"
4. Follow the configuration steps. You'll need to provide your Panasonic ID and your password. The integration will discover the devices associated to your Panasonic ID. 

### Manual installation
1. Copy the folder named `aquarea` from the [latest release](https://github.com/cjaliaga/home-assistant-aquarea/releases/latest) to the `custom_components` folder in your config folder.
2. Restart Home Assistant
3. Add integration via (one of them):
   - [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aquarea)
   - Go to "Settings" >> "Devices & Services", click "+ ADD INTEGRATION" and select "Aquarea Smart Cloud"
4. Follow the configuration steps. You'll need to provide your Panasonic ID and your password. The integration will discover the devices associated to your Panasonic ID.

## Warning
This integration is currently in beta. It supports several devices but it has been tested with a single device. If you have multiple devices under the same Panasonic ID, please test it and report any issue you find.

The integration also supports devices with several zones, but it has not been tested with multiple zones. If you have a device with multiple zones, please test it and report any issue you find.

The integration has been tested with a heat pump with a hot water tank, but it has not been tested with a heat pump without a hot water tank. If you have a heat pump without a hot water tank, please test it and report any issue you find.

## Disclaimer

THIS PROJECT IS NOT IN ANY WAY ASSOCIATED WITH OR RELATED TO PANASONIC. The information here and online is for educational and resource purposes only and therefore the developers do not endorse or condone any inappropriate use of it, and take no legal responsibility for the functionality or security of your devices.

## Acknowledgements and alternatives

Big thanks to [ronhks](https://github.com/ronhks) for his awesome work on the [Panasonic Aquaera Smart Cloud integration with MQTT](https://github.com/ronhks/panasonic-aquarea-smart-cloud-mqtt). You can use his integration if you want to use MQTT instead.
