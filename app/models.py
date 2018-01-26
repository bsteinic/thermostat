from app import db

# My database table SetTemp
class ThermConfig(db.Model):
  name = db.Column(db.String(64), primary_key=True)
  value = db.Column(db.String(120), index=True, unique=False)
  
  # For printing out the object when debugging
  def __repr__(self):
    return '<CfgItem %r %r>' % (self.name, self.value)

# My database table SetTemp
class SetTemp(db.Model):
  id   = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
  type = db.Column(db.String(16), index=True, unique=False)
  day  = db.Column(db.Integer, index=True, unique=False)
  hour = db.Column(db.Integer, index=True, unique=False)
  minute  = db.Column(db.Integer, index=True, unique=False)
  setTemp = db.Column(db.Integer, index=False, unique=False)
  
  # For printing out the object when debugging
  def __repr__(self):
    return '<SetTemp %r>' % (self.id)

class CurTemp(db.Model):
  Date = db.Column(db.String(32), primary_key=True, nullable=False)
  Temp = db.Column(db.String(8), index=False, unique=False)
  
  # For printing out the object when debugging
  def __repr__(self):
    return '<SetTemp %r>' % (self.Date)

class Vacation(db.Model):
  id  = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
  startDateTime = db.Column(db.String(20))
  endDateTime = db.Column(db.String(20))
  setTemp = db.Column(db.Integer, index= False, unique=False)
  
  # For printing out the object when debugging
  def __repr__(self):
    return '<Vacation %r>' % (self.id)
