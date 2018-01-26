#!flask/bin/python
import os, re
import sys
import glob
from pytz import timezone
import pytz
from transitions import Machine
import datetime
from datetime import timedelta
import random
import time
from app import db, models, enable_global_distpackages
from daemon import Daemon
import subprocess

# Switch to True to debug on non Pi system.
TestMode = False

inactiveHysteresis = 0.0
activeHysteresis = 0.0

ac_inactiveHysteresis = 0.0
ac_activeHysteresis = 0.0

cfgItem = models.ThermConfig.query.get('HEATER_PIN')
HEATER_PIN=int(cfgItem.value, 10)
cfgItem = models.ThermConfig.query.get('AC_PIN')
AC_PIN=int(cfgItem.value, 10)
cfgItem = models.ThermConfig.query.get('FAN_PIN')
FAN_PIN=int(cfgItem.value, 10)

g_pingCheckCount=1
g_pingDown=0
g_curTempCount=0

log = open("logs/debug_" + datetime.datetime.now().strftime('%Y%m%d') + ".log", "a")
dStr = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# This test must have been hanging when the wifi goes south???
# If we get a miss check twice to be sure 
def isNetUp():
  host = "192.168.0.1"
  r = "".join(os.popen("ping " + host + " -c 1").readlines())
  if re.search("64 bytes from", r):
    return True
  else:
    time.sleep(1)
    r = "".join(os.popen("ping " + host + " -c 1").readlines())
    if re.search("64 bytes from", r):
      return True
    else:
      return False
  

# setup stuff for reading temperature on real hardware
if TestMode == False:
  enable_global_distpackages()
  import RPi.GPIO as GPIO
  os.system('modprobe w1-gpio')
  os.system('modprobe w1-therm')

  base_dir = '/sys/bus/w1/devices/'
  device_folder = glob.glob(base_dir + '28*')[0]
  device_file = device_folder + '/w1_slave'

# My Finite State Machine
# define states and transitions
# trigger must return True for state to change
# source where the trigger applies
# before: execute prior to changing state only if trigger == True
# after: execute after changing state
# dest: state to change to
states = ['off', 'idle_heat', 'idle_ac', 'heat_on', 'ac_on']
transitions = [
  {
      'trigger': 'switch_to_heat',
      'source':  ['off', 'idle_ac', 'idle_heat'],
      'before':  'all_off',
      'dest':    'idle_heat'
  },
  {
      'trigger': 'switch_to_heat',
      'source':  'heat_on',
      'dest':    'heat_on'
  },
  {
      'trigger': 'switch_to_heat',
      'source':  'ac_on',
      'before':  'blow_out',
      'after':   'all_off',
      'dest':    'idle_heat'
  },
  {
      'trigger': 'switch_to_ac',
      'source':  ['off', 'idle_heat', 'idle_ac'],
      'before':  'all_off',
      'dest':    'idle_ac'
  },
  {
      'trigger': 'switch_to_ac',
      'source':  'ac_on',
      'dest':    'ac_on'
  },
  {
      'trigger': 'switch_to_ac',
      'source':  'heat_on',
      'before':  'blow_out',
      'after':   'all_off',
      'dest':    'idle_ac'
  },
  {
      'trigger': 'switch_to_off',
      'source':  ['off', 'idle_heat', 'idle_ac'],
      'after':   'all_off',
      'dest':    'off'
  },
  {
      'trigger': 'switch_to_off',
      'source':  ['heat_on','ac_on'],
      'before':  'blow_out',
      'after':   'all_off',
      'dest':    'off'
  },
  {
      'trigger':    'check_temp',
      'source':     'off',
      'dest':       'off',
      'after':      'update_temp',
      'conditions': 'sample_temp',
  },
  {
      'trigger':    'check_temp',
      'source':     'idle_ac',
      'dest':       'ac_on',
      'after':      'ac_active',
      'conditions': 'temp_above_ac_set_temp'
  },
  {
      'trigger':    'check_temp',
      'source':     'ac_on',
      'dest':       'idle_ac',
      'before':     'blow_out',
      'after':      'all_off',
      'conditions': 'temp_below_ac_set_temp'
  },
  {
      'trigger':    'check_temp',
      'source':     'idle_heat',
      'dest':       'heat_on',
      'after':      'heat_active',
      'conditions': 'temp_below_heat_set_temp'
  },
  {
      'trigger':    'check_temp',
      'source':     'heat_on',
      'dest':       'idle_heat',
      'before':     'blow_out',
      'after':      'all_off',
      'conditions': 'temp_above_heat_set_temp'
  },
]

# Utility Functions
def readTempRaw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
  
def getCurTemp():
  global dStr
  global log
  global g_curTempCount
  
  if TestMode == True:
    temp_f = (random.randint(680, 780) * 0.1)
  else:
    lines = readTempRaw()
    count = 0
    while (count < 10) and (lines[0].strip()[-3:] != 'YES'):
      time.sleep(0.2)
      lines = read_temp_raw()
    if count >= 10:
      log.write (dStr + ", Failed to read temp\n")
      return int(72)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
      temp_string = lines[1][equals_pos+2:]
      temp_c = float(temp_string) / 1000.0
      temp_f = temp_c * 9.0 / 5.0 + 32.0

    cur_set_temp = models.ThermConfig.query.get('cur_temp')
    cur_set_temp.value = temp_f
    db.session.commit()
    log.write(dStr + ", Current Temp " + str(cur_set_temp.value) + "\n")
    if (g_curTempCount % 8) == 0:
      cur_temp = models.CurTemp(Date=dStr, Temp=temp_f)
      db.session.add(cur_temp)
      db.session.commit()
      count = models.CurTemp.query.count()
      if count > 7168:
        lim = count - 7168
        if lim > 0:
          del_temp = models.CurTemp.query.order_by(models.CurTemp.Date.asc()).limit(lim).all()
          for dt in del_temp:
            db.session.delete(dt)
          db.session.commit()
    g_curTempCount = g_curTempCount + 1
    return float(temp_f)

# Based on the current date/time get the first set temperature time prior to now
def getSetTemp(type):
  global dStr
  global log
  cur_set_temp = models.ThermConfig.query.get('set_temp')
  t = datetime.datetime.now()
  dateStr = t.strftime('%Y-%m-%d %H:%M')
  d = t.weekday()
  h = t.time().hour
  m = t.time().minute
  
  # check for a vacation temperature setting first
  # the vacation temp holds the temperature until that time
  # Start Date/Time, End Data/Time, setTemp
  strf = '((startDateTime <= \'' + dateStr + '\') and (endDateTime >= \'' + dateStr + '\'))'
  vacTemp = models.Vacation.query.filter(strf).order_by('startDateTime asc').first()
  # find an entry whose startDate <= now and now <= endDate
  if vacTemp is not None:
    log.write(dStr + ' vacation ' + vacTemp.startDateTime + ' cmp with ' + dateStr + '\n')
    if str(vacTemp.setTemp) != cur_set_temp.value:
      cur_set_temp.value = vacTemp.setTemp
      db.session.commit()
    return float(vacTemp.setTemp)
  
  # check for a hold temperature setting first
  # the hold temp holds the temperature until that time
  chk_type = 'Hold'
  strf = '(type == \'' + chk_type +'\')'
  setTemp = models.SetTemp.query.filter(strf).order_by('hour asc').first()
  if setTemp is not None:
    if (int(setTemp.hour) <= int(h)) and (int(setTemp.minute) <= int(m)) or (int(setTemp.hour) < int(h)):
      log.write(dStr + ' removing hold temp\n')
      db.session.delete(setTemp)
      db.session.commit()
    if str(setTemp.setTemp) != str(cur_set_temp.value):
      cur_set_temp.value = setTemp.setTemp
      db.session.commit()
    return float(setTemp.setTemp)
  
  chk_type = type
  strf = '(type == \'' + chk_type +'\') AND ((day == ' + str(d) + ' AND hour == ' + str(h) + ' AND minute <= ' + str(m) + ') OR (day == ' + str(d)+ ' AND hour < ' + str(h) + ') '
  if (d > 0):
    strf = strf + 'OR (day < ' + str(d) + '))'
    stro = 'day desc, hour desc, minute desc'
  else:
    strf = strf + 'OR (day == 6))'
    stro = 'day asc, hour desc, minute desc'
  
  setTemp = models.SetTemp.query.filter(strf).order_by(stro).first()
  if str(setTemp.setTemp) != str(cur_set_temp.value):
    log.write( dStr +  ", SetTemp is " + str(setTemp.setTemp) + "\n")
    cur_set_temp.value = setTemp.setTemp
    db.session.commit()
  return float(setTemp.setTemp)

class Thermostat(Daemon):
  heat = False
  ac   = False
  fan  = False
  fan_auto = True
  debug = True
  blow_out_secs = 70
  
  # Debug
  def print_status(self):
    if self.heat == True:
      str = "H"
    else:
      str = "h"
    if self.ac == True:
      str = str + "A"
    else:
      str = str + "a"
    if self.fan == True:
      str = str + "F"
    else:
      str = str + "f"
    t = datetime.datetime.now()
    log.write( t.strftime("%Y-%m-%d %H:%M:%S") + ", Status " + str + "\n")
  
  def configureGPIO(self):
    if TestMode == False:
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(HEATER_PIN, GPIO.OUT)
      GPIO.setup(AC_PIN, GPIO.OUT)
      GPIO.setup(FAN_PIN, GPIO.OUT)
      subprocess.Popen("echo " + str(HEATER_PIN) + " > /sys/class/gpio/export", shell=True)
      subprocess.Popen("echo " + str(AC_PIN) + " > /sys/class/gpio/export", shell=True)
      subprocess.Popen("echo " + str(FAN_PIN) + " > /sys/class/gpio/export", shell=True)

  # Conditions
  def sample_temp(self):
    curTemp = getCurTemp()
    return False

  def temp_above_ac_set_temp(self):
    global ac_inactiveHysteresis
    curTemp = getCurTemp()
    if curTemp > (getSetTemp('Cool') + ac_inactiveHysteresis):
      return True
    return False
  
  def temp_below_ac_set_temp(self):
    global ac_activeHysteresis
    curTemp = getCurTemp()
    if curTemp  < (getSetTemp('Cool') - ac_activeHysteresis):
      return True
    return False
  
  def temp_above_heat_set_temp(self):
    global activeHysteresis
    curTemp = getCurTemp()
    if curTemp > (getSetTemp('Heat') + activeHysteresis):
      return True
    return False
  
  def temp_below_heat_set_temp(self):
    global inactiveHysteresis
    global dStr
    curTemp = getCurTemp()
    if curTemp < (getSetTemp('Heat') - inactiveHysteresis):
      log.write(dStr + ", " + str(curTemp) + " < " + str(getSetTemp('Heat')) + " - " + str(inactiveHysteresis) + "\n")
      return True
    return False
  
  # Before and After Actions
  def update_temp(self):
    curTemp = getCurTemp()
  
  def quies_gpio(self):
    if TestMode == False:
      self.heat = self.ac = self.fan = False
      self.update_gpio()

  def update_gpio(self):
    global dStr
    global log
    if TestMode == False:
      GPIO.setmode(GPIO.BCM)
      GPIO.setup(HEATER_PIN, GPIO.OUT)
      GPIO.setup(AC_PIN, GPIO.OUT)
      GPIO.setup(FAN_PIN, GPIO.OUT)
      log.write(dStr + ", update gpio " + str(self.heat) + str(self.ac) +str(self.fan) + "\n")
      GPIO.output(HEATER_PIN, self.heat)
      GPIO.output(AC_PIN, self.ac)
      GPIO.output(FAN_PIN, self.fan)

  def blow_out(self):
    global dStr
    global log
    self.heat = False
    self.ac   = False
    fan_state = self.fan
    self.fan  = False
    self.update_gpio()
    if self.debug:
      self.print_status()
    log.write(dStr + ", Blow out for " + str(self.blow_out_secs) + "\n")
    time.sleep(1)
    self.fan = fan_state
    self.update_gpio()
    #time.sleep(self.blow_out_secs)
  
  def heat_active(self):
    self.heat = True
    self.update_gpio()
    if self.debug:
      self.print_status()
  
  def ac_active(self):
    self.ac = True
    self.update_gpio()
    if self.debug:
      self.print_status()
  
  def all_off(self):
    self.heat = False
    self.ac   = False
    if self.fan_auto:
      self.fan = False
    if self.debug:
      self.print_status()
    self.update_gpio()
  
  def set_fan_on(self):
    self.fan_auto = False
    self.fan = True
    self.update_gpio()
    if self.debug:
      self.print_status()
  
  def set_fan_auto(self):
    self.fan_auto = True
    self.fan = False
    self.update_gpio()
    if self.debug:
      self.print_status()
  
  def set_debug_on(self):
    self.debug = True
  
  def set_debug_off(self):
    self.debug = False
  
  def run(self):
    global log
    global dStr
    global ac_inactiveHysteresis
    global ac_activeHysteresis
    global inactiveHysteresis
    global activeHysteresis
    global g_pingCheckCount
    global g_pingDown
    therm.configureGPIO()

    machine = Machine(model=therm, states=states, transitions=transitions, initial='off')

    cfgItem = models.ThermConfig.query.get('active_hysteresis')
    activeHysteresis = float(cfgItem.value)
    cfgItem = models.ThermConfig.query.get('inactive_hysteresis')
    inactiveHysteresis = float(cfgItem.value)

    cfgItem = models.ThermConfig.query.get('ac_active_hysteresis')
    ac_activeHysteresis = float(cfgItem.value)
    cfgItem = models.ThermConfig.query.get('ac_inactive_hysteresis')
    ac_inactiveHysteresis = float(cfgItem.value)

    log = open("logs/debug_" + datetime.datetime.now().strftime('%Y%m%d') + ".log", "a")
    now = datetime.datetime.now()
    dStr = now.strftime("%Y-%m-%d %H:%M:%S")
    log.write(dStr + ", Starting\n")
    
    fan_switch = models.ThermConfig.query.get('fan_switch')
    prev_fan_val = fan_switch.value
    mode_switch = models.ThermConfig.query.get('mode_switch')
    prev_mode_switch_val = mode_switch.value
    prev_therm_state = therm.state
    log.write(dStr + " Mode:" + prev_mode_switch_val + " Fan:" + " State:" + therm.state +"\n")
    log.write(dStr + "Active/Inactive Hysteresis " + str(activeHysteresis) + "/" + str(inactiveHysteresis) + '\n')
    if mode_switch.value == 'Heat':
      therm.switch_to_heat()
      log.write(dStr + " Mode switched to Heat" + "\n")
    elif mode_switch.value == 'Cool':
      therm.switch_to_ac()
      log.write(dStr + " Mode switched to Cool" + "\n")
    else:
      therm.switch_to_off()
      log.write(dStr + " Mode switched to Off" + "\n")
    log.close()
    # The Loop
    while True:
      now = datetime.datetime.now()
      dStr = now.strftime("%Y-%m-%d %H:%M:%S")

      log = open("logs/debug_" + datetime.datetime.now().strftime('%Y%m%d') + ".log", "a")
      # Check for configuration changes
      #  Thermostate: Heating, Cooling or Off
      #  Fan: Auto, On
      mode_switch = models.ThermConfig.query.get('mode_switch')
      if mode_switch.value != prev_mode_switch_val:
        if mode_switch.value == 'Heat':
          therm.switch_to_heat()
          log.write(dStr + " Mode switched to Heat" + "\n")
        elif mode_switch.value == 'Cool':
          therm.switch_to_ac()
          log.write(dStr + " Mode switched to Cool" + "\n")
        else:
          therm.switch_to_off()
          log.write(dStr + " Mode switched to Off" + "\n")
        prev_mode_switch_val = mode_switch.value
      
      fan_switch = models.ThermConfig.query.get('fan_switch')
      if fan_switch.value != prev_fan_val:
        if fan_switch.value == 'On':
          therm.set_fan_on()
        else:
          therm.set_fan_auto()
        prev_fan_val = fan_switch.value 
      #log.write(dStr + " Fan switch prev:" + prev_fan_val + "  New:" + fan_switch.value + "\n")

      #if mode_switch.value != 'Off':
      if therm.check_temp():
        if therm.state != prev_therm_state:
          prev_therm_state = therm.state
          log.write(dStr + " State changed to " + therm.state + "\n")
          
      # Reboot system if 3 consecutive pings to the router fail
      # checking roughly every 1 minutes
      # must be down for 3 consecutive minutes
      if (g_pingCheckCount % 6) == 0:
        if isNetUp() == False:
          g_pingDown = g_pingDown + 1
          if g_pingDown > 4:
            log.write(dStr + ' NETWORK IS DOWN 6 min Issue Reboot\n')
            therm.quies_gpio()
            command = "/usr/bin/sudo /sbin/reboot"
            process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            output = process.communicate()[0]
            log.write(dStr + output)
          else:
            if g_pingDown > 2:
              log.write(dStr + ' NETWORK IS DOWN for 3 min unbind\n')
              command = "echo 1-1.4 > /sys/usb/drivers/usb/unbind; sleep 0.5; echo 1-1.4 > /sys/usb/drivers/usb/bind"
              process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
              output = process.communicate()[0]
              log.write(dStr + output + '\n')
      #      log.close()
      #      therm.stop()
        else:
          g_pingDown = 0
      g_pingCheckCount = g_pingCheckCount + 1
      
      future = now + datetime.timedelta(0,10)
      end = datetime.datetime.now()
      d_secs = future - end
      #log.write(dStr + 'Sleep for ' + str(d_secs.seconds) + '\n')
      log.close()
      db.session.expire_all()
      time.sleep(10)


# Starting
if __name__ == "__main__":
  therm = Thermostat('myFSM.pid')
  #therm.run()
  #sys.exit(0)
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      therm.start()
    elif 'stop' == sys.argv[1]:
      log.write(dStr + ", Stop" + "\n")
      #stop all HVAC activity when daemon stops
      therm.quies_gpio()
      therm.stop()
    elif 'restart' == sys.argv[1]:
      log.write(dStr + ", Restart\n")
      therm.restart()
    else:
      print "Unknown command"
      sys.exit(2)
    sys.exit(0)
  else:
    print "usage: %s start|stop|restart" % sys.argv[0]
    sys.exit(2)

