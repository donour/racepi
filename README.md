____  ______              ______ _ 
\ \ \ | ___ \             | ___ (_)
 \ \ \| |_/ /__ _  ___ ___| |_/ /_ 
  > > >    // _` |/ __/ _ \  __/| |
 / / /| |\ \ (_| | (_|  __/ |   | |
/_/_/ \_| \_\__,_|\___\___\_|   |_|
=================

RacePi is a software system for recording racecar sensor data on a Raspberry Pi. A variety of sensors sources are supported and it is easy to add more. The system is currently designed with autocross in mind with automatic record triggers. RacePi is implemented primary in Python with a few components in SQL and C.

Software Components
---------------------
1. **SQLite Database:** Standardized schema for sensor data 
2. **Sensor Recorder:** Multiprocessing, multithreaded data logging program
3. **Web-based Analysis Tool:** On-device webserver for performing immediate analysis and plotting
4. **Device Controls:** Misc software tools for managing the device


Supported Sensor Sources
---------------------
* GPS velocity and position via gpsd
* Pi Sense Hat IMU
* HS CAN bus readers


Copyright and License
---------------------
RacePi is licensed under the [GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html), version 2 only.
