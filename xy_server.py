# -*- coding: utf-8 -*-
"""
@author: Robert Rehammar

An xy-table server
This server checks that the motors are avaialble and sets up a VISA server to respond to any incomming commands.

Copyright (c) 2016 Qamcom Research and Technology

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

from visa_server import Visaserver
import sys
import getopt
from xy_table import Xy_table, XyTableError, XyTableWarning
from time import sleep

def error_cb():
    print("error cb called")

def test_cb(params, extra_params):
    print("test cb")

def move(params, extra_params):
    '''
    Move a distance given in parameters using the current unit set in settings.
    '''
    table = extra_params[0]
    step_distances = params[0]
    (dx,dy) = step_distances.split(',')
    if settings['unit'] == 'steps':
        try:
            table.move_steps(int(dx), int(dy))
        except XyTableWarning as w:
            print(w)
    else:
        try:
            table.move_m(float(dx)/units[settings['units']],
                         float(dy)/units[settings['units']])
        except XyTableWarning as w:
            print(w)
        except KeyError as e:
            print('got unknown unit')

def set_unit(params, extra_params):
    '''
    Set which units communicated values between server and client should be in.
    '''
    new_unit = params[0]
    settings = extra_params[0]
    units = extra_params[1]

    # Check that the server knows about the unit
    try:
        units[new_unit]
    except KeyError as e:
        print("Got unknown unit ('%s'), keeping current ('%s')"%(new_unit, settings['unit']))
    else:
        settings['unit'] = new_unit

def opc(params, extra_params):
    table = extra_params[0]
    if table.is_moving():
        return "0"
    else:
        return "1"
        
def main(argv):
    '''
    Main program
    '''
    try:
       opts, args = getopt.getopt(argv,"hi:",["idn="])
    except getopt.GetoptError:
       print('usage: python3 xy_server.py -h for help')
       sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('usage: python3 xy_server.py')
            sys.exit(0)
        elif opt in ('-i', '--idn'):
            idn = arg
    
    print('Starting server...')
    with Xy_table(async = True) as table:
        while True:
            try:
                with Visaserver(idn = "Qamcom XY table v0.1") as server:
                    # Create all callbacks for the xy-table
#                    server.set_callback("test", test_cb, error_cb, [])
                    server.set_callback("move:rel", move, error_cb, [table])
                    server.set_callback("set:unit", set_unit, error_cb, [settings, units])
                    server.set_callback("*opc?", opc, error_cb, [table])
                    server.run()
            except OSError as e:
                print("I'm too fast, need to remake the server.")
                sleep(0.2)

if __name__ == '__main__':
    settings = dict()
    units = dict()
    settings['unit'] = 'steps'
    units['m'] = 1
    units['steps'] = 1
    units['dm'] = 10
    units['cm'] = 100
    units['mm'] = 1000

    main(sys.argv[1:])
