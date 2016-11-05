RacePi
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

Hardware Recommendations
------------------------

RacePi can be used to build a full-featured datalogging system with modest hardware and very little cost. This requires:

1. **Raspberry Pi 3: $35** Any Raspberry Pi model will work, but the latest version brings a significant performance benfit
2. **Pi Sense Hat: $40** The Pi Sense Hat was designed for data collection on the International Space Station. It contains sensors for a 9-dof IMU, as well as 5 button joystick and an 8x8 LED array for displaying status.
3. **GPS Receiver: $30** RacePi works with any Linux-compatible GPS receiver. High speed drone receivers are available for cheap on Amazon.
3. **CAN Adapter: $30+** RacePi has built-in support for the STN11XX chipset, used in devices like the OBDLink SX. Other adapters can be easily added.
4. **SD card + USB stick: $5** Storage for the software and data logs
5. **Micro USB Power Source: $3** The system needs a power source capable of delivering a reliable 5v @ 1.5A.


Copyright and License
---------------------
RacePi is licensed under the [GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html), version 2 only.
