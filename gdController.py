from flask import Flask,jsonify,json,request
app = Flask(__name__)
import wiringpi
import time
import socket
import netifaces as ni
import os

import secret #imports settings

# https://github.com/shekarpathi/RaghuGarageDoorPython/blob/master/gdController.py
# https://pinout.xyz/pinout/wiringpi#

control_pin = 25
control_pin_2 = 22
wiringpi.wiringPiSetup()
wiringpi.pinMode(control_pin, 0) # Initialize as input mode so that it does not send any pulse
wiringpi.pinMode(control_pin_2, 0) # Initialize as input mode so that it does not send any pulse

counter = 0

@app.route("/reboot")
def rebootPi():
        os.system('sudo shutdown -r now')

@app.route("/")
def hello():
        global counter
        counter = counter + 1
        if (counter == 9999):
                counter=1
        return str(counter) + ": This IP, " + getRemoteIP() + ", will be reported to the US Federal Authorities for prosecution"

@app.route("/press/<door>", methods=['POST'])
def actOnDoor(door):
        #send_email('Pressed '+door+ ' door', 'press method called', getRemoteIP())
        secretHeader = request.headers.get('secretHeader')
        if secretHeader:
                if secretHeader == secret.HEADER_PASSWORD:
                        if (door == 'single'):
                                return toggleDoor(control_pin)
                        if (door == 'double'):
                                return toggleDoor(control_pin_2)
                else:
                        return "secret contains invalid value. " + warningString()
        else:
                return "secret not present. " + warningString()

def warningString():
        return "This IP, " + getRemoteIP() + ", will be reported to the US Federal Authorities for prosecution"

def toggleDoor(pin):
        try:
                print("Sending a pulse")
                wiringpi.pinMode(pin, 1) # sets GPIO output just in time before sending a pulse
                wiringpi.digitalWrite(pin, 1)
                wiringpi.digitalWrite(pin, 0)
                time.sleep(0.5)
                wiringpi.digitalWrite(pin, 1)
                wiringpi.pinMode(pin, 0) # sets GPIO as input so that no spurious output signals are sent
                print("Sent a pulse")
                send_email('GarageDoor Controller sent a pulse', 'toggle method called', getRemoteIP())
                return "Sent a pulse"
        except Exception, e:
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
        send_email('Garage opener python program started', 'curl -H "secretHeader: ' + secret.HEADER_PASSWORD + '" -X POST http://raghupi.local:5001/press/single\n', 'startup script')
        app.run(host = '0.0.0.0',port=5001)
