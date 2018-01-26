from app import app
from app import db
from app.models import ThermConfig, SetTemp, Vacation, CurTemp
import os
import subprocess
import datetime
from flask import Flask, jsonify, redirect, url_for, render_template, request, flash
from flask.ext.wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms import StringField, IntegerField, validators
from wtforms.validators import DataRequired

import pygal

from myFSM import TestMode


# Get Static Configuration Items
cfgItem = ThermConfig.query.get('weather_enabled')
if cfgItem.value == 'True':
  weatherEnabled = True
else:
  weatherEnabled = False
cfgItem = ThermConfig.query.get('zip_code')
zipCode = cfgItem.value
cfgItem = ThermConfig.query.get('HEATER_PIN')
heater_pin = cfgItem.value
cfgItem = ThermConfig.query.get('AC_PIN')
ac_pin = cfgItem.value
cfgItem = ThermConfig.query.get('FAN_PIN')
fan_pin = cfgItem.value

# define some support functions
if weatherEnabled == True:
  import pywapi
  def getWeather():
        result = pywapi.get_weather_from_yahoo( str(zipCode), units = 'imperial' )
        string = result['html_description']
        string = string.replace("\n", "")

        #You will likely have to change these strings, unless you don't mind the additional garbage at the end.
        string = string.replace("(provided by <a href=\"http://www.weather.com\" >The Weather Channel</a>)<br/>", "")
        string = string.replace("<br /><a href=\"http://us.rd.yahoo.com/dailynews/rss/weather/Nashville__TN/*http://weather.yahoo.com/forecast/USTN0357_f.html\">Full Forecast at Yahoo! Weather</a><BR/><BR/>", "")
        return string

def getOperStatus():
  cfgItem = ThermConfig.query.get('set_temp')
  set_temp = cfgItem.value
  cfgItem = ThermConfig.query.get('cur_temp')
  cur_temp = cfgItem.value

  if TestMode == False:
    heatStatus = int(subprocess.Popen("cat /sys/class/gpio/gpio" + str(heater_pin) + "/value", shell=True, stdout=subprocess.PIPE).stdout.read().strip())
    acStatus = int(subprocess.Popen("cat /sys/class/gpio/gpio" + str(ac_pin) + "/value", shell=True, stdout=subprocess.PIPE).stdout.read().strip())
    fanStatus = int(subprocess.Popen("cat /sys/class/gpio/gpio" + str(fan_pin) + "/value", shell=True, stdout=subprocess.PIPE).stdout.read().strip())
  else:
    heatStatus = 0
    acStatus = 0
    fanStatus = 0

  dStr=["OFF", "ON"]
  operStatus = []
  operStatus.append(cur_temp)
  operStatus.append(set_temp)
  operStatus.append(dStr[heatStatus])
  operStatus.append(dStr[acStatus])
  operStatus.append(dStr[fanStatus])

  return operStatus

def getThermostatStatus():
  try:
    with open('myFSM.pid'):
      pid = int(subprocess.Popen("cat myFSM.pid", shell=True, stdout=subprocess.PIPE).stdout.read().strip())
      try:
        os.kill(pid, 0)
        return "<div id=\"daemonRunning\"> Thermostat is running. </div>"
      except OSError:
        return "<div id=\"daemonNotRunning\"> Thermostat status UNKNOWN. </div>"
  except IOError:
    return "<div id=\"daemonNotRunning\"> Thermostat IS NOT RUNNING. </div>"

def getSchedule():
  mode_switch = ThermConfig.query.get('mode_switch')
  oStr = 'day asc, hour asc, minute asc'
  if mode_switch.value == 'Heat':
    oStr = 'type desc, ' + oStr
  else:
    oStr = 'type asc, ' + oStr
  sched = SetTemp.query.order_by(oStr).all()
  return sched

def getScheduleById(id):
  sched = SetTemp.query.filter('id == \''+ id +'\'').first()
  return sched

def deleteScheduleById(id):
  sched = getScheduleById(id)
  db.session.delete(sched)
  db.session.commit()

def addSched(Form):
  title = StringField("Add Schedule Item", validators[DataRequired()])


def getVacations():
  oStr = 'startDateTime asc'
  vacation = Vacation.query.order_by(oStr).all()
  return vacation

def getVacationById(id):
  vacation = Vacation.query.filter('id == \''+ id +'\'').first()
  return vacation

def deleteVacationById(id):
  vacation = getVacationById(id)
  db.session.delete(vacation)
  db.session.commit()

def addVacationItem(Form):
  title = StringField("Add Vacation Item", validators[DataRequired()])

# Views
@app.route('/_update', methods=['GET'])
def update():
  mode_switch = ThermConfig.query.get('mode_switch')
  fan_switch = ThermConfig.query.get('fan_switch')
  fanStr = "Fan:"+fan_switch.value
  operstatus=getOperStatus()
  return jsonify(fanMode=fanStr, mode=mode_switch.value, curTemp=operstatus[0], setTemp=operstatus[1], heat=operstatus[2], ac=operstatus[3], fan=operstatus[4])

@app.route('/')
@app.route('/index')
def index():
  weatherString = "ooo"
  if weatherEnabled == True:
    try:
      weatherString = getWeather()
      print weatherString
    except:
      weatherString = "Couldn't get remote weather info! <br><br>"
  thermostatStatus = getThermostatStatus()
  operStatus = getOperStatus()
  return render_template("index.html", title = 'Home', \
                                       weatherString = weatherString, \
                                       thermostatStatus = thermostatStatus, \
                                       operStatus = operStatus)

@app.route('/index', methods=['POST'])
@app.route('/', methods=['POST'])
def index_post():
  return redirect('/index')
  
@app.route('/mode/<mode>')
def mode_switch_set(mode):
  mode_switch = ThermConfig.query.get('mode_switch')
  mode_switch.value = mode
  db.session.commit()
  return redirect('/index')

@app.route('/fanmode/<mode>')
def fan_switch_set(mode):
  mode_switch = ThermConfig.query.get('fan_switch')
  mode_switch.value = mode
  db.session.commit()
  return redirect('/index')

@app.route('/bump/<type>/<minutes>')
def bump_temp(type, minutes):
  t = datetime.datetime.now()
  d = t.weekday()
  h = t.time().hour
  m = t.time().minute

  mode_switch = ThermConfig.query.get('mode_switch')
  t_min = (int(m) + int(minutes)) % 60
  hr = int(h) + (int(m) + int(minutes)) / 60

  setTemp = SetTemp.query.filter('type == \'Hold\'').count()
  if setTemp > 0:
    # We already have a Hold just update the time???
    return redirect('/index')

  cfgItem = ThermConfig.query.get('set_temp')

  cur_set_temp = ThermConfig.query.get('set_temp')
  if mode_switch.value == 'Heat':
    newTemp = int(cfgItem.value) + 2
    flash('New temp is set to ' + str(newTemp))
    cur_set_temp.value = newTemp
    setTemp = SetTemp(type='Hold', day=0, hour=int(hr), minute=t_min, setTemp=newTemp)
  elif mode_switch.value == 'Cool':
    newTemp = int(cfgItem.value) - 2
    cur_set_temp.value = newTemp
    setTemp = SetTemp(type='Hold', day=0, hour=int(hr), minute=t_min, setTemp=newTemp)
  else:
    return redirect('/index')
    
  db.session.add(setTemp)
  db.session.commit()
  flash('Thanks for adding a set temp schedule item.')
  return redirect('/index')

# Vacation
@app.route('/viewEditVacation')
def viewEditVacation():
  vacations = getVacations()
  return render_template("vacation.html", title='VacationEdit', vacations = vacations)

class VacationForm(Form):
  id        = IntegerField('startDate')
  startDate = StringField('startDate', validators=[DataRequired()])
  startTime = StringField('startTime', validators=[DataRequired()])
  endDate   = StringField('endDate', validators=[DataRequired()])
  endTime   = StringField('endTime', validators=[DataRequired()])
  setTemp   = IntegerField('setTemp', validators=[DataRequired()])

@app.route('/addVacation', methods=['GET', 'POST'])
def addVacation():
  model = Vacation(setTemp=45)
  form = VacationForm()
  if request.method == 'POST':
    #flash('Thanks for adding a set vacation item.')
    startDateTime = form.startDate.data + ' ' + form.startTime.data
    endDateTime = form.endDate.data + ' ' + form.endTime.data
    vacation = Vacation(startDateTime=startDateTime, endDateTime=endDateTime, setTemp=form.setTemp.data)
    db.session.add(vacation)
    db.session.commit()
    return redirect('/viewEditVacation')
  
  set_temp_choices=range(45,80)
  
  return render_template("addVacation.html", title='VacationEdit', set_temp_choices=set_temp_choices, setTemp = model.setTemp)

@app.route('/deleteVacation/<id>')
def deleteVacation(id):
  deleteVacationById(id)
  return redirect(url_for('viewEditVacation'))

@app.route('/editVacation/<id>', methods=['GET', 'POST'])
def editVacation(id):
  model = Vacation.query.get(id)
  form = VacationForm(request.form)
  
  if request.method == 'POST':
    #flash('Thanks for updating a vacation item.')
    model.startDateTime = form.startDate.data + ' ' + form.startTime.data
    model.endDateTime = form.endDate.data + ' ' + form.endTime.data
    model.setTemp = form.setTemp.data
    db.session.commit()
    return redirect('/viewEditVacation')
  (form.startDate.data,form.startTime.data) = str(model.startDateTime).split(' ')
  (form.endDate.data,form.endTime.data) = str(model.endDateTime).split(' ')
  form.setTemp.data = model.setTemp
  
  set_temp_choices=range(45,80)
  
  return render_template("editVacation.html", title='VacationEdit', id=id, startDate=form.startDate.data, startTime=form.startTime.data, endDate=form.endDate.data, endTime=form.endTime.data, set_temp_choices=set_temp_choices, setTemp=model.setTemp)

#  MyForm = model_form(Vacation, Form)
#  model = Vacation.query.get(id)
#  form = MyForm(request.form, model)
#  
#  if request.method == 'POST':
#    form.populate_obj(model)
#    vacation = Vacation(id=id, startDateTime=form.startDateTime.data, endDateTime=form.endDateTime.data, setTemp=form.setTemp.data)
#    db.session.commit()
#    return redirect('/viewEditVacation')
#  set_temp_choices=range(45,80)
#  return render_template("editVacation.html", title='VacationEdit', id=id, startDateTime=model.startDateTime, endDateTime=model.endDateTime, set_temp_choices=set_temp_choices, setTemp = model.setTemp)


# Schedule
@app.route('/viewEditSchedule')
def viewEditSchedule():
  dayOfWeek=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday", "Sunday"]
  sched = getSchedule()
  return render_template("sched.html", title='ScheduleEdit', dayOfWeek = dayOfWeek, sched = sched)

@app.route('/addSchedule/<type>', methods=['GET', 'POST'])
def addSchedule(type):
  MyForm = model_form(SetTemp, Form)
  model = SetTemp.query.filter('type == \'Heat\'').first()
  form = MyForm(request.form, model)
  if request.method == 'POST':
  #if form.validate_on_submit():
    #flash('Add Schedule Item')
    setTemp = SetTemp(type=form.type.data, day=form.day.data, hour=form.hour.data, minute=form.minute.data, setTemp=form.setTemp.data)
    db.session.add(setTemp)
    db.session.commit()
    #flash('Thanks for adding a set temp schedule item.')
    return redirect('/viewEditSchedule')
  
  type_choices=['Heat', 'Cool', 'Hold']
  dayOfWeek=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday", "Sunday"]
  day_choices=range(7)
  hour_choices=range(24)
  minute_choices=range(0, 60, 5)
  set_temp_choices=range(45,80)
  
  t = datetime.datetime.now()
  d = t.weekday()
  h = t.time().hour
  m = t.time().minute
  
  return render_template("addSchedule.html", title='ScheduleEdit', type_choices=type_choices, type=type, dayOfWeek = dayOfWeek, day_choices=day_choices, hour=h, hour_choices=hour_choices, minute_choices=minute_choices, minute=m, set_temp_choices=set_temp_choices, setTemp = model.setTemp)

@app.route('/deleteSchedule/<id>')
def deleteSchedule(id):
  deleteScheduleById(id)
  return redirect(url_for('viewEditSchedule'))

@app.route('/editSchedule/<id>', methods=['GET', 'POST'])
def editSched(id):
  MyForm = model_form(SetTemp, Form)
  model = SetTemp.query.get(id)
  form = MyForm(request.form, model)

  if request.method == 'POST':
    form.populate_obj(model)
    setTemp = SetTemp(id=id, type=form.type.data, day=form.day.data, hour=form.hour.data, minute=form.minute.data, setTemp=form.setTemp.data)
    db.session.commit()
    flash("Updated Item")
    return redirect('/viewEditSchedule')
  type_choices=['Heat', 'Cool', 'Hold']
  day_choices=range(7)
  hour_choices=range(24)
  minute_choices=range(0, 60, 5)
  set_temp_choices=range(45,80)
  dayOfWeek=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday", "Sunday"]
  return render_template("editSchedule.html", title='ScheduleEdit', type_choices=type_choices, type=model.type, dayOfWeek = dayOfWeek, day_choices=day_choices, day=model.day, hour=model.hour, hour_choices=hour_choices, minute_choices=minute_choices, minute=model.minute, set_temp_choices=set_temp_choices, setTemp = model.setTemp)


@app.route('/chart/<limit>')
def chart(limit=7168):
  limit = int(limit)
  if limit < 256:
    limit = 256
  elif limit > 7168:
    limit = 7168
  line_chart = pygal.Line(show_dots=False, show_legend=False, x_label_rotation=90, show_minor_x_labels=False,  x_labels_major_every=int(limit/28))
  line_chart.title = 'Temperature'
  temps = CurTemp.query.order_by(CurTemp.Date.asc())[-limit:]
  labels=[]
  cTemps=[]
  for t in temps:
    labels.append(t.Date)
    cTemps.append(float(t.Temp))
  line_chart.x_labels = labels
  line_chart.add('Temp', cTemps)
  chart = line_chart.render(is_unicode=True)
  return render_template('chart.html', chart=chart)

@app.route('/line_chart.svg')
def graph_it():
  return line_chart.render_response()

