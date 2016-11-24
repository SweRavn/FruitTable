#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 19 12:48:36 2016

@author: Robert Rehammar

This class only support moving the table in units of steps or metre. Owner needs to translate to other units.

"""


# TODO: Make a linear translator sub-class for each dimension.


"""
while (True):
	print("Single coil steps")
	myStepper.step(100, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.SINGLE)
	myStepper.step(100, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.SINGLE)
	print("Double coil steps")
	myStepper.step(100, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.DOUBLE)
	myStepper.step(100, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.DOUBLE)
	print("Interleaved coil steps")
	myStepper.step(100, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.INTERLEAVE)
	myStepper.step(100, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.INTERLEAVE)
	print("Microsteps")
	myStepper.step(100, Adafruit_MotorHAT.FORWARD, Adafruit_MotorHAT.MICROSTEP)
	myStepper.step(100, Adafruit_MotorHAT.BACKWARD, Adafruit_MotorHAT.MICROSTEP)
"""

import time
import atexit
import sys
import json
import threading
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperMotor

FORWARD = Adafruit_MotorHAT.FORWARD
BACKWARD = Adafruit_MotorHAT.BACKWARD

SINGLE = Adafruit_MotorHAT.SINGLE
DOUBLE = Adafruit_MotorHAT.DOUBLE
INTERLEAVE = Adafruit_MotorHAT.INTERLEAVE
MICROSTEP = Adafruit_MotorHAT.MICROSTEP

class XyTableError(Exception):
    def __init__(self, info_str):
        self._info_str = info_str
    def __str__(self):
        return self._info_str

class XyTableWarning(Exception):
    def __init__(self, info_str):
        self._info_str = info_str
    def __str__(self):
        return self._info_str
        
class Xy_table:
    def __init__(self,
                 settings_file = None,
#                 x_min_ms_gpio = None,
#                 x_max_ms_gpio = None,
#                 y_min_ms_gpio = None,
#                 y_max_ms_gpio = None,
                 motor_hat_i2c_address = None, # I2C HAT address, default is 0x60
                 x_length_m = None, # Travel length of table in x-dim
                 y_length_m = None,
                 x_stepping = None, # Stepping method; SINGLE, DOUBLE, INTERLEAVE, MICROSTEP
                 y_stepping = None,
                 x_steps_per_rev = None, # Number of steps per rev in SINGEL step mode
                 y_steps_per_rev = None,
                 x_speed = None, # How fast the motor should be made to go, rpm
                 y_speed = None,
                 x_motor_id = None, # Motor id in x-dim, 1 or 2.
                 boundary_check = True, # Using knowledge of current position and table size to check boundaries.
                 x_thread_pitch = None, # Thread pitch of threaded rod in x-dim (m). M6 has 1 mm.
                 y_thread_pitch = None, # Thread pitch of threaded rod in y-dim (m).
                 async = False, # Control if move should be blocking or not.
                 ):

        self.__boundary_check = boundary_check
        self.__async = async
        
        # Read setting from file
        if settings_file:
            self._settings_file = settings_file
        else:
            self._settings_file = '.xy_table_settings.json'
        try:
            with open(self._settings_file, 'r') as infile:
                self._settings = json.load(infile)
        except FileNotFoundError:
            self._settings = dict()

        # FIXME: read this from file or init it from microswitches and check that it is know or halt
        #self._settings['current_x'] = 2000
        #self._settings['current_y'] = 0

        # Create the stepper motor objects:
        try:
            self._settings['x_motor_id']
        except KeyError:
            if not x_motor_id in [1, 2]:
                raise XyTableError("'x_motor_id' not properly set (should be 1 or 2), cannot continue.")
            else:
                self._settings['x_motor_id'] = x_motor_id
        self._settings['y_motor_id'] = 3 - self._settings['x_motor_id']

        # Check motor steps per rev:
        if x_steps_per_rev:
            self._settings['x_steps_per_rev'] = x_steps_per_rev
        try:
            self._settings['x_steps_per_rev']
        except KeyError:
            raise XyTableError("'x_steps_per_rev' not set, cannot continue.")
        if y_steps_per_rev:
            self._settings['y_steps_per_rev'] = y_steps_per_rev
        try:
            self._settings['y_steps_per_rev']
        except KeyError:
            raise XyTableError("'y_steps_per_rev' not set, cannot continue.")
        
        if motor_hat_i2c_address == None:
            motor_hat_i2c_address = 0x60
        # Create a default object, no changes to I2C address or frequency
        self._mh = Adafruit_MotorHAT(addr = motor_hat_i2c_address)

        # Recommended for auto-disabling motors on shutdown
        atexit.register(self.turnOffMotors)

        # Create motor objects
        self.__x_mult = 2 if self._settings['x_stepping'] == INTERLEAVE else 8 if self._settings['x_stepping'] == MICROSTEP else 1
        self.__y_mult = 2 if self._settings['y_stepping'] == INTERLEAVE else 8 if self._settings['y_stepping'] == MICROSTEP else 1
        self.__sx = self._mh.getStepper(self._settings['x_steps_per_rev']*self.__x_mult, self._settings['x_motor_id'])
        self.__sy = self._mh.getStepper(self._settings['y_steps_per_rev']*self.__y_mult, self._settings['y_motor_id'])

        # Set stepping
        if x_stepping in [SINGLE, DOUBLE, INTERLEAVE, MICROSTEP]:
            self._settings['x_stepping'] = x_stepping
        try:
            self._settings['x_stepping']
        except KeyError:
            self._settings['x_stepping'] = MICROSTEP
            print('Warning: stepping choice in x wrong, will use micro stepping in x') # FIXME: make a logging instead...
        if y_stepping in [SINGLE, DOUBLE, INTERLEAVE, MICROSTEP]:
            self._settings['y_stepping'] = y_stepping
        try:
            self._settings['y_stepping']
        except KeyError:
            self._settings['y_stepping'] = MICROSTEP
            print('Warning: stepping choice in y wrong, will use micro stepping in y') # FIXME: make a logging instead...

        # Set speed of motors
        if x_speed:
            self._settings['x_speed'] = x_speed
        else:
            try:
                self._settings['x_speed']
            except KeyError:
                self._settings['x_speed'] = 60
                print('No x_speed given, using default 60 rpm')
        if y_speed:
            self._settings['y_speed'] = y_speed
        else:
            try:
                self._settings['y_speed']
            except KeyError:
                self._settings['y_speed'] = 60
                print('No y_speed given, using default 60 rpm')
        self.__sx.setSpeed(self._settings['x_speed']*self.__x_mult)
        self.__sy.setSpeed(self._settings['y_speed']*self.__y_mult)

        """
        # Initiate the microswitches:
        # FIXME: sätt vissa portat till inportar.
        # FIXME_ läs in vilka switchar som används från settings eller från parametrar
        # FIXME: not used at the moment
        try:
            self.__settings['x_min_ms_gpio']
        except ValueError:
            if not x_min_ms_gpio:
                raise XyTableError("'x_min_ms_gpio' not set, cannot continue.")
            else:
                self.__settings['x_min_ms_gpio'] = x_min_ms_gpio

        try:
            self.__settings['x_max_ms_gpio']
        except ValueError:
            if not x_max_ms_gpio:
                raise XyTableError("'x_max_ms_gpio' not set, cannot continue.")
            else:
                self.__settings['x_max_ms_gpio'] = x_max_ms_gpio

        try:
            self.__settings['y_min_ms_gpio']
        except ValueError:
            if not y_min_ms_gpio:
                raise XyTableError("'y_min_ms_gpio' not set, cannot continue.")
            else:
                self.__settings['y_min_ms_gpio'] = y_min_ms_gpio

        try:
            self.__settings['y_max_ms_gpio']
        except ValueError:
            if not y_max_ms_gpio:
                raise XyTableError("'y_max_ms_gpio' not set, cannot continue.")
            else:
                self.__settings['y_max_ms_gpio'] = y_max_ms_gpio
            
        self.__x_min_ms = x min micro switch pin
        self.__x_max_ms = ...
        self.__y_min_ms =
        self.__y_max_ms = """
        
        # Check if physical table size is known
        if x_length_m:
            self._settings['x_length_m'] = x_length_m
        try:
            self._settings['x_length_m']
        except KeyError:
            raise XyTableError("'x_length_m' not properly set, cannot continue.")
        if y_length_m:
            self._settings['y_length_m'] = y_length_m
        try:
            self._settings['y_length_m']
        except KeyError:
            raise XyTableError("'y_length_m' not properly set, cannot continue.")

        # Check threading
        if x_thread_pitch:
            self._settings['x_thread_pitch'] = x_thread_pitch
        try:
            self._settings['x_thread_pitch']
        except KeyError:
            raise XyTableError("'x_thread_pitch' not properly set, cannot continue.")
        if y_thread_pitch:
            self._settings['y_thread_pitch'] = y_thread_pitch
        try:
            self._settings['y_thread_pitch']
        except KeyError:
            raise XyTableError("'y_thread_pitch' not properly set, cannot continue.")

        # Compute scaling factor
        self._scale_x = self._settings['x_steps_per_rev']/self._settings['x_thread_pitch'] # Steps per meter
        self._scale_y = self._settings['y_steps_per_rev']/self._settings['y_thread_pitch'] # Steps per meter

        # Compute tabele size in steps from other data.
        self._x_length_steps = round(self._settings['x_length_m']*self._scale_x) # Table length in x in steps
        self._y_length_steps = round(self._settings['y_length_m']*self._scale_y) # Table length in y in steps

        print('Current positions is: ', self._settings['current_x'] , self._settings['current_y'])
        print('Table size in steps is (x, y): ', self._x_length_steps, self._y_length_steps)
                
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._settings_file:
            with open(self._settings_file, 'w') as outfile:
                json.dump(self._settings, outfile, sort_keys=True, indent=4)

    def turnOffMotors(self):
        print("Exiting")
        self._mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
        self._mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
        self._mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
        self._mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)

    def goto_position_m(self, x, y, blocking = False):
        '''
        Goto a position defined by distance in m.
        Does not do boundary checks, that is left to low level function.
        
        blocking If True, call will not return until new position is set. Default False
        '''
        if not (self._settings['x_length_m'] and self._settings['x_length_m']):
            raise XyTableWarning('Absolute table length not known, can not make movement in m.')
        
        x_steps = round(self._scale_x*x) # Could keep rounding error...
        y_steps = round(self._scale_y*y)
        
        self.goto_position_steps(x_steps, y_steps, blocking)
        
    def goto_position_steps(self, x, y, blocking = False):
        '''
        Goto a positions defined by distance in steps.
        blocking If True, call will not return until new position is set. Default False
        '''
        steps_x = x - self._settings['current_x']
        steps_y = y - self._settings['current_y']
        self.move_steps(steps_x, steps_y)
        
    def __move(self, stepper, numsteps, direction, stepping_style):
        """
    	Low level move function. Operating in steps.
    	"""
        stepper.step(numsteps, direction, stepping_style)

    def move_m(self, m_x, m_y):
        '''
        Move m_x, m_y metre.
        '''
        steps_x = round(self._scale_x*m_x) # Could keep rounding error...
        steps_y = round(self._scale_y*m_y)
        return self.move_steps(steps_x, steps_y)
        
    def move_steps(self, steps_x, steps_y):
        '''
    	Move staps_x, steps_y steps.
    	'''
        # Check that another move commend is not being executed
        try:
            self.__stx
        except:
            pass
        else:
            if self.__stx.is_alive() or self.__sty.is_alive():
                raise XyTableWarning('Table is already moving. Move canceled.')

        x = self._settings['current_x'] + steps_x
        y = self._settings['current_y'] + steps_y
        print('new pos: (x,y), steps (dx, dy): ', x, y, steps_x, steps_y)
        if self.__boundary_check:
            if x > self._x_length_steps or \
               y > self._y_length_steps or \
               x < 0 or \
               y < 0:
                raise XyTableWarning('Position outside of table, can not make movement.')

        x_direction = BACKWARD if steps_x > 0 else FORWARD
        y_direction = BACKWARD if steps_y < 0 else FORWARD
        steps_x = abs(steps_x)
        steps_y = abs(steps_y)

        print(steps_x, self.__x_mult)
        print(steps_y, self.__y_mult)

        self.__stx = threading.Thread(target=self.__move, args=(self.__sx,
                                                          steps_x*self.__x_mult,
                                                          x_direction, self._settings['x_stepping']))
        self.__stx.start()
        self.__sty = threading.Thread(target=self.__move, args=(self.__sy,
                                                          steps_y*self.__y_mult,
                                                          y_direction, self._settings['y_stepping']))
        self.__sty.start()
        if not self.__async:
            while self.__stx.is_alive() or self.__sty.is_alive():
                # Is synchronous operation is requested, wait until all threads have finished.
                pass
        # FIXME: do some checking that we made all steps before setting new position
        self._settings['current_x'] = x
        self._settings['current_y'] = y
        
    def get_position(self):
        # FIXME: update _current_x and _current_y from threads if there are any.
        return self._current_x, self._current_y
        
    def set_x_length(self, x_length_m):
        '''
        Set the linear travel distance in x-direction in m
        '''
        self._settings['x_length_m'] = x_length_m

    def set_y_length(self, y_length_m):
        '''
        Set the linear travel distance in y-direction in m
        '''
        self._settings['y_length_m'] = y_length_m
    
    def init_positions(self):
        '''
        Initiate the table by going to the end position and count the table size if required.
        '''
        
        # Fetch the table width in steps.
        try:
            self._settings['x_steps']
        except KeyError:
            pass
            # FIXME: need to measure how many steps the tabe is
        
        try:
            self._settings['y_steps']
        except KeyError:
            pass
            # FIXME: samma

def main(argv):
    print("main")
    with Xy_table(x_motor_id = 1,
                  x_steps_per_rev = 200,
                  y_steps_per_rev = 200,
                  x_stepping = MICROSTEP,
                  y_stepping = MICROSTEP,
#                  x_stepping = SINGLE,
#                  y_stepping = SINGLE,
                  x_speed = 120,
                  y_speed = 120) as tbl:
#        tbl.goto_position_steps(4000, 100)
        tbl.move(500, 1000)
        print("test") 
        
if __name__ == "__main__":
    main(sys.argv[1:])
