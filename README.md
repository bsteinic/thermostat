Thermostat
==========
Materials needed to create thermostat hardware.
-----------------------------------------------
-    36.00  Raspberry Pi
- x  59.99  Raspberry Pi B+ w/case wifi pwr supply
-   25.00  24V AC SSR Board assembled w/components
- x  18.00  24V AC SSR Board w/components
-    10.00  24V AC SSR Board
- x   4.89  DS18B20 Thermistor
- x   0.05  4.7K Ohm Resistor
    

Components on SSR Board
-----------------------
I got mine from Makeatronics 
http://makeatronics.blogspot.com/2013/06/24v-ac-solid-state-relay-board.html
- 3  BT134-600E.127  TRIAC 600V 4A SOT82
- 3  MOC3063         OPTOISO 600VDRM TRIAC ZC 6-DIP
- 3  WP3A8GD         LED SS 3MM 568NM GRN DIFF
- 6  CF14JT560R      RES 560 OHM 1/4W 5% CARBON FILM
- 3  CF14JT100R      RES 100 OHM 1/4W 5% CARBON FILM
- 1  1935239         TERM BLOCK PCB 9POS 5.0MM GREEN

Hardware Connections set in config.txt
- HEATER_PIN = 22
- AC_PIN = 17
- FAN_PIN = 27

| BCM/CPU |    BOARD          | Conn |  LED    | Furnace | 
|---------|:------------------|-----:|:--------|:--------|
| GPIO 17 |   pin 11 === A/C  |    1 |  Yellow | Yellow  | 
| GPIO 27 |   pin 13 === Fan  |    2 |  Green  | Green   | 
| GPIO 22 |   pin 15 === Heat |    3 |  Red    | White   | 
|         |               Hot |      |         | Red     |
|         |               Com |      |         |         |

C  24VAC com  COM- 
Y  A/C        1 yel led
G  Fan        2 grn led
W  Heat       3 red led
R  24VAC hot  HOT 

Thermistor DS18B20
Use (1) 2.2K upto 4.7K Ohm resistor between pin 2 and 3.

| Therm |             | Raspberry Pi         |       |
| Pin   | Description | Pin                  | RJ-45 |
|-------|:------------|:---------------------|:------|
| 1     | Ground      | 9, Ground Black wire | pin 6 |
| 2     | data GPIO4  | 7, Yellow wire       | pin 3 |
| 3     | 3V          | 1, red wire 3.3V     | pin 4 |

RJ45 Connector Pin

red-----3
yellow--2  D bottom
black---1

RJ-45 to db9 wiring diagram
1 = Blue
2 = Orange
3 = Black
4 = Red
5 = Green
6 = Yellow
7 = Brown
8 = White

added dtoverlay=w1-gpio-pullup to /boot/config.txt
% sudo vi /etc/modules  add w1-gpio and w1_therm
% sudo modprobe w1-gpio
% sudo modprobe w1-therm
% cd /sys/bus/w1/devices
% ls
% cd 28-*
% cat w1_slave

Temperature sensor
Yellow
Black
Red

WiFI Dropout issues try editing 
% sudo vi /etc/modprobe.d/8192cu.conf
paste following lines
# Disable power saving
options 8192cu rtw_power_mgnt=0 rtw_enusbss=1 rtw_ips_mode=1

% sudo reboot

To automatically start the thermostat install the thermostat.sh found in
pi/ directory into /etc/init.d

Installing and enabling watchdog
put in /etc/init.d/thermostat
sudo modprobe bcm2708_wdog
add 
echo "bcm2708_wdog" | sudo tee -a /etc/modules
sudo apt-get install watchdog
sudo update-rc.d watchdog defaults
sudo vi /etc/watchdog.conf
uncomment 
#max-load-1 = 24
sudo /etc/init.d watchdog start

Software
--------
Raspbian distribution
% sudo apt-get install python-flask
kernel modules: w1-gpio, w1-therm
% sudo apt-get install python-sqlite sqlite3
% sudo apt-get install python-pip 
% sudo pip install pywapi
had to 
% wget https://launchpad.net/python-weather-api/trunk/0.3.8/+download/pywapi-0.3.8.tar.gz
then:
% python setup.py build
%python setup.py install
%sudo pip install feedparser

Setting TZ
% sudo dpkg-reconfigure tzdata

virtual env setup
-----------------
```
% sudo apt-get install python-virtualenv
% virtualenv flask
% flask/bin/pip install flask
% flask/bin/pip install flask-login
% flask/bin/pip install flask-openid
% flask/bin/pip install flask-mail
% flask/bin/pip install flask-sqlalchemy
% flask/bin/pip install sqlalchemy-migrate
% flask/bin/pip install flask-whooshalchemy
% flask/bin/pip install flask-wtf
% flask/bin/pip install flask-babel
% flask/bin/pip install guess_language
% flask/bin/pip install flipflop
% flask/bin/pip install coverageUse 
% pip install flask-sqlalchemy
% pip install flask-wtf
% pip install pygal
% pip install pytz
% pip install transitions
```

thereafter just use `% source flask/bin/activate`

```
wget http://downloads.raspberrypi.org/raspbian_latest
wget https://github.com/wywin/Rubustat/archive/master.zip
```

edit config.txt.template as config.txt
edit mailconfg.txt.template as mailconf.txt

??? edit /etc/modules adding w1_therm.ko and w1-gpio.ko

added these lines to /etc/rc.local
```
modprobe w1-gpio
modprobe w1-therm or w1_therm
```
To start the application `% sudo /etc/init.d/thermostat start`

Installing 
----------
cp this directory and its contents to the /home/pi directory
there is a set of db python scripts to set defaults for the app.db

```
cp pi/thermostat file to /etc/init.d/thermostat
% sudo update-rc.d thermostat defaults
```

MacOS installing OS on SD 
-------------------------
see www.raspberrypi.org/documentation/installation/installing-images/mac.md
```
% diskutil list
```
identify the disk of your SD diskN
```
% diskutil umount Disk /dev/diskN
% sudo dd bs=1m if=image.img of=/dev/diskN
% sudo diskutil eject /dev/diskN
```

Thermostat database
-------------------
login/password dbuser/db@authroot
see app/models.py for table descriptions

error_reporting(E_ALL);
ini_set('display_errors', true);

for syntax errors check tail -f /var/log/lighttpd/error.log

2015_12_07 Monday
-----------------
The wifi stopped working again. Unplugged the wifi adapter and plugged it
back in. The thermo website still was unreachable but I could reboot via ssh.

It's a RT5370 Wireless Adapter
There is a problem from the /var/log/kern.log file:
Dec  7 20:54:14 raspberrypi kernel: [502039.914797] wlan0: associated
Dec  7 21:11:50 raspberrypi kernel: [503096.074242] ieee80211 phy0:
rt2x00usb_vendor_request: Error - Vendor Request 0x06 failed for offset 0x101c
with error -110
Dec  7 21:11:50 raspberrypi kernel: [503096.174274] ieee80211 phy0:
rt2x00usb_vendor_request: Error - Vendor Request 0x07 failed for offset 0x101c
with error -110
Dec  7 21:11:51 raspberrypi kernel: [503096.274268] ieee80211 phy0:
rt2x00usb_vendor_request: Error - Vendor Request 0x07 failed for offset 0x101c
with error -110
Dec  7 21:11:51 raspberrypi kernel: [503096.374284] ieee80211 phy0:
rt2x00usb_vendor_request: Error - Vendor Request 0x06 failed for offset 0x101c
with error -110

Checking out the kernel source...
see /usr/share/doc/raspberrypi-bootloader/
changelog
zcat changelog.Debian.gz

fwhash=$(zcat /usr/share/doc/changelog.Debian.gz | grep -m 1 'as of' | awk
'{print $NF}')
linuxhash=$(wget -qO-
https://raw.github.com/raspberrypi/firmware/$fwhash/extra/git_hash)
git checkout $linuxhash

building the source on ubuntu...
`% sudo apt-get -y update
% sudo apt-get -y install build-essential git
% cd
% git clone git://github.com/raspberrypi/linux.git
% git clone git://github.com/raspberrypi/tools.git
% scp pi@X.X.X.X:\{/usr/share/doc/raspberrypi-bootloader/changelog.Debian.gz,/proc/config.gz\} .`
substitute your Pi's address for X.X.X.X, 
then enter your Pi's password; default is "raspberry")
`% cd ~/linux
% fwhash=$(zcat ~/changelog.Debian.gz | grep -m 1 'as of' | awk '{print $NF}')
% linuxhash=$(wget -qO- http://raw.github.com/raspberrypi/firmware/$fwhash/extra/git_hash)
% git checkout $linuxhash
% make mrproper
% zcat ~/config.gz > ./.config
% make ARCH=arm menuconfig`
choose your kernel options; M means module, * means built into kernel
`% make ARCH=arm CROSS_COMPILE=~/tools/arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian/bin/arm-linux-gnueabihf- -k
% mkdir -p modules
% make modules_install ARCH=arm INSTALL_MOD_PATH=modules CROSS_COMPILE=~/tools/arm-bcm2708/gcc-linaro-arm-linux-gnueabihf-raspbian/bin/arm-linux-gnueabihf-`

You will find the modules in ~/linux/modules/lib/modules/*/kernel, and you
can copy them to your Pi using
`% scp moduleName pi@X.X.X.X:`
Once on your Pi, you can move or copy them from your home folder to the
corresponding place inside /lib/modules/*/kernel.

If you want to use the newly built kernel, then on Ubuntu, type:
`% cd ~/tools/mkimage
% ./imagetool-uncompressed.py ~/linux/arch/arm/boot/zImage
% scp kernel.img pi@X.X.X.X: `
Once the new kernel is on your Pi, you can move or copy it from your home
folder to /boot, and restart to use it. I strongly recommend you first
rename /boot/kernel.img to something like /boot/kernel_orig.img first so
you can revert to it if needed.

Changed the /boot/cmdline.txt from:
dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p8 rootfstype=ext4 elevator=deadline rootwait
to
dwc_otg.fiq_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p8 rootfstype=ext4 elevator=deadline rootwait

Still hanging
Jan 14 14:31:20 raspberrypi kernel: [323136.746171] ieee80211 phy0: rt2800usb_tx_sta_fifo_read_completed: Warning - TX status read failed -71
Jan 14 14:32:00 raspberrypi kernel: [323176.571732] ieee80211 phy0: rt2x00usb_vendor_request: Error - Vendor Request 0x07 failed for offset 0x7010 with error -110

thermostat continues to function but have lost contact via USB wifi and
keyboard.

2015_02_20 Friday
-----------------
Was having a problem with the USB hanging on the pi...

HOORAY!!!!!

Upraded the raspberry pi OS and it has been running like a champ ever since.
So they must have fixed the USB driver bug that was causing the hang.
% sudo apt-get upgrade
% sudo rpi-update
Had to update /boot/config.txt
added
device_tree_overlay=overlays/w1-gpio-pullup-overlay.dtb
Been up for 14 days
pi@raspberrypi ~/src/thermostat/logs $ uptime
 16:02:34 up 14 days,  3:07,  1 user,  load average: 0.14, 0.16, 0.21

pi@raspberrypi ~/src/thermostat/logs $ uname -a
Linux raspberrypi 3.18.5+ #748 PREEMPT Wed Feb 4 21:24:41 GMT 2015 armv6l GNU/Linux



