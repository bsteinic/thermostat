from app import db, models

def initDefaults():
  cfg = models.ThermConfig(name='HEATER_PIN', value='22')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='AC_PIN', value='17')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='FAN_PIN', value='27')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='weather_enabled', value='True')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='email_enabled', value='False')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='active_hysteresis', value='1.3')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='inactive_hysteresis', value='0.5')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='zip_code', value='84037')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='debug_enabled', value='True')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='mode_switch', value='Heat')
  db.session.add(cfg)
  db.session.commit()
  cfg = models.ThermConfig(name='fan_switch', value='Auto')
  db.session.add(cfg)
  db.session.commit()

def createDefaultSchedule():
  db.session.add_all([
    models.SetTemp(id = 1, type="Heat", day=0, hour= 6, minute=15, setTemp=68),
    models.SetTemp(id = 2, type="Heat", day=0, hour=22, minute=45, setTemp=64),
    models.SetTemp(id = 3, type="Heat", day=1, hour= 6, minute=15, setTemp=68),
    models.SetTemp(id = 4, type="Heat", day=1, hour=22, minute=45, setTemp=64),
    models.SetTemp(id = 5, type="Heat", day=2, hour= 6, minute=15, setTemp=68),
    models.SetTemp(id = 6, type="Heat", day=2, hour=22, minute=45, setTemp=64),
    models.SetTemp(id = 7, type="Heat", day=3, hour= 6, minute=10, setTemp=68),
    models.SetTemp(id = 8, type="Heat", day=3, hour=22, minute=45, setTemp=64),
    models.SetTemp(id = 9, type="Heat", day=4, hour= 6, minute=30, setTemp=68),
    models.SetTemp(id =10, type="Heat", day=4, hour=23, minute=30, setTemp=64),
    models.SetTemp(id =11, type="Heat", day=5, hour= 6, minute=15, setTemp=68),
    models.SetTemp(id =12, type="Heat", day=5, hour=23, minute=00, setTemp=64),
    models.SetTemp(id =13, type="Heat", day=6, hour= 7, minute=30, setTemp=68),
    models.SetTemp(id =14, type="Heat", day=6, hour=11, minute=00, setTemp=60),
    models.SetTemp(id =15, type="Heat", day=6, hour=14, minute=10, setTemp=68),
    models.SetTemp(id =16, type="Heat", day=6, hour=22, minute=15, setTemp=64),
    models.SetTemp(id =17, type="Cool", day=0, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =18, type="Cool", day=0, hour=22, minute=30, setTemp=72),
    models.SetTemp(id =19, type="Cool", day=1, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =20, type="Cool", day=1, hour=22, minute=30, setTemp=72),
    models.SetTemp(id =21, type="Cool", day=2, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =22, type="Cool", day=2, hour=22, minute=30, setTemp=72),
    models.SetTemp(id =23, type="Cool", day=3, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =24, type="Cool", day=3, hour=22, minute=30, setTemp=72),
    models.SetTemp(id =25, type="Cool", day=4, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =26, type="Cool", day=4, hour=23, minute=30, setTemp=72),
    models.SetTemp(id =27, type="Cool", day=5, hour= 6, minute=30, setTemp=74),
    models.SetTemp(id =28, type="Cool", day=5, hour=23, minute=00, setTemp=72),
    models.SetTemp(id =29, type="Cool", day=6, hour= 7, minute=00, setTemp=74),
    models.SetTemp(id =30, type="Cool", day=6, hour=11, minute=00, setTemp=78),
    models.SetTemp(id =31, type="Cool", day=6, hour= 2, minute=00, setTemp=74),
    models.SetTemp(id =32, type="Cool", day=6, hour=22, minute=15, setTemp=72),
    ])
  db.session.commit()

initDefaults()
createDefaultSchedule()
