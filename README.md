# FruitTable
Raspberry Pi/Adafruit Motor HAT xy table driver and VISA sever written in Python.

See the file test.py for how the xy table class can be used.

See xy_server.py for how the visa server and the xy table are combined to for an xy table that can be remote controlled.

Designed for Raspberry Pi with the Adafriut Motor HAT, two stepper motors and an xy-table.

Requires python 3, but should be easy to modofy to run using Python 2.

Usage:
python3 xy_server.py

Then it is possible to connect with VISA using raw socket or just a raw TCP/IP socket.

Several parameters needs to be provided at first run. These are later stored in a settings json file for future reference.

