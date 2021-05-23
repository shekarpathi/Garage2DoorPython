from flask import Flask,jsonify,json,request

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["20 per day", "10 per hour"]
)

import wiringpi
import time
import socket
import netifaces as ni

import secret #imports settings

# https://bitbucket.org/kamushekar/garageraspi/src/master/gdController.py
# https://pinout.xyz/pinout/pin32_gpio12

control_pin = 25
control_pin_2 = 22
wiringpi.wiringPiSetup()
wiringpi.pinMode(control_pin, 0) # Initialize as input mode so that it does not send any pulse
wiringpi.pinMode(control_pin_2, 0) # Initialize as input mode so that it does not send any pulse

counter = 0

@app.route("/five")
@limiter.limit("2 per minute")
def two():
    return "2 per minute!"

@app.route("/")
def hello():
        global counter
        counter = counter + 1
        return str(counter)

@app.route("/on1", methods=['GET'])
@limiter.limit("2 per minute")
def actOnDoor1():
#        send_email('Pressed /on1', 'press method called', getRemoteIP())
        secretHeader = request.headers.get('secret')
        if secretHeader:
		if secretHeader == secret.HEADER_PASSWORD:
			return toggleDoor(control_pin)
		else:
			return "secret contains invalid value. " + warningString()
        else:
		return "secret not present. " + warningString()

@app.route("/on2", methods=['GET'])
@limiter.limit("2 per minute")
def actOnDoor2():
#        send_email('Pressed /on2', 'press method called', getRemoteIP())
	secretHeader = request.headers.get('secret')
	if secretHeader:
		if secretHeader == secret.HEADER_PASSWORD:
			return toggleDoor(control_pin_2)
		else:
			return "secret contains invalid value. " + warningString()
	else:
		return "secret not present. " + warningString()

@app.route("/state", methods=['GET'])
def getState():
#        send_email('/state', 'press method called', getRemoteIP())
        secretHeader = request.headers.get('secret')
        if secretHeader:
		if secretHeader == secret.HEADER_PASSWORD:
			return "0"
		else:
			return "secret contains invalid value. " + warningString()
        else:
		return "secret not present. " + warningString()

def warningString():
        return "This IP, " + getRemoteIP() + ", will be reported to the US Federal Authorities for prosecution"

def toggleDoor(pin):
	try:
		print("Sending a pulse on ")
		wiringpi.pinMode(pin, 1) # sets GPIO output just in time before sending a pulse
		wiringpi.digitalWrite(pin, 1)
		wiringpi.digitalWrite(pin, 0)
		time.sleep(0.5)
		wiringpi.digitalWrite(pin, 1)
		wiringpi.pinMode(pin, 0) # sets GPIO as input so that no spurious output signals are sent
		print("Sent a pulse")
		send_email('GarageDoor Controller sent a pulse', 'toggle method called', getRemoteIP())
		return "1"
        except Exception, e:
                return "-1"
                print str(e)

def getRemoteIP():
        if request.headers.getlist("X-Forwarded-For"):
                ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
                ip = request.remote_addr
        return ip

# Function to display hostname and
# IP address
def get_Host_name_IP():
    try:
        ni.ifaddresses('wlan0')
        ip = ni.ifaddresses('wlan0')[ni.AF_INET][0]['addr']
        print ip
        send_email('Pi\'s IP address ' + ip, 'IP address Raghupi', 'startup script')
    except:
        print("Unable to get Hostname and IP")

def send_email(subject, body, ip):
    import smtplib

    gmail_user = secret.GMAIL_USER
    gmail_app_password = secret.GMAIL_PASS
    FROM = secret.GMAIL_FROM_ADDRESS
    #TO = [secret.TO_ADDRESS_EMAIL, secret.TO_ADDRESS_NUMBER, secret.TO_ADDRESS_EMAIL_2, secret.TO_ADDRESS_NUMBER_2]
    TO = [secret.TO_ADDRESS_EMAIL, secret.TO_ADDRESS_NUMBER]
    SUBJECT = subject
    TEXT = body + "\n IP:" + ip

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        # SMTP_SSL Example
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo() # optional, called by login()
        server_ssl.login(gmail_user, gmail_app_password)
        # ssl server doesn't support or need tls, so don't call server_ssl.starttls()
        server_ssl.sendmail(FROM, TO, message)
        #server_ssl.quit()
        server_ssl.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"

if __name__ == "__main__":
        get_Host_name_IP() #Function call
	hostnamev = socket.gethostname()
	print(hostnamev)
        send_email(secret.SECRET_STARTUP_MESSAGE, 'curl -H "secret: ' + secret.HEADER_PASSWORD + '" -X GET http://' + hostnamev + '.local:5002/on1\n', 'startup script')
        app.run(host = '0.0.0.0',port=5002)
