#!flask/bin/python
import subprocess
from app import app

# Start the background process daemon
app.secret_key = 'nobody will guess'
app.config['SESSION_TYPE'] = 'filesystem'
print 'Starting myFSM'
subprocess.Popen("flask/bin/python myFSM.py start", shell=True)
app.run(host="0.0.0.0", debug=True)
