#!/usr/bin/env python
import os, sys, getopt, getpass
import RPi.GPIO as GPIO
import time
import traceback

def turnOn(pin, seconds):
  GPIO.setmode(GPIO.BCM)

  GPIO.setup(pin, GPIO.OUT)

  GPIO.output(pin, True)
  time.sleep(seconds)
  GPIO.output(pin, False)

  GPIO.cleanup()

def main():
  # parse command line options
  try:
    optlist, args = getopt.getopt(sys.argv[1:], 'h?g:t:', ['help','h','?'])
  except getopt.error, msg:
    print msg
    print "for help use --help"
    sys.exit(2)
  # process options
  options = dict(optlist)
  if len(args) > 1:
    print 'len(args):'+str(len(args))
    print "for help use --help ;)"
    sys.exit(3)
  if '-g' in options:
    gpioPin = int(options['-g'])
  if '-t' in options:
    seconds = int(options['-t'])

  turnOn(gpioPin, seconds)
  exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print str(e)
        traceback.print_exc()
        sys.exit(1)
