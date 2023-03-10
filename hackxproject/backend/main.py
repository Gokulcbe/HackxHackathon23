import hashlib
import json
import logging
import os

from random import randint

import mpu
import mysql.connector
import requests

from colorama import Fore, Style, init
from flask import Flask, request
from flask_cors import CORS
from waitress import serve

app = Flask(__name__)
CORS(app)

init(autoreset=True)


# Logger custom formatter

class CustomFormatter(logging.Formatter):
    green = Fore.GREEN
    yellow = Fore.YELLOW
    red = Fore.RED
    bold_red = Style.BRIGHT + Fore.RED
    reset = Fore.RESET
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: green + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Initialise logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialise console logger

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)
c_handler.setFormatter(CustomFormatter())
logger.addHandler(c_handler)

# Initialise file logger

f_handler = logging.FileHandler('routing.log')
f_handler.setLevel(logging.DEBUG)
f_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"))
logger.addHandler(f_handler)


@app.after_request
def Log(response):
    info = str(request.environ.get('HTTP_X_FORWARDED_FOR', '')) + "==" + str(request.endpoint) + "==" + str(response.status)
    logging.info(info)
    return response


@app.route('/PostRegisterContractor', methods=['POST'])
def RegisterContractor():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users WHERE EmailID = '" +
                     request.form['email'] + "'")
    myresultEmail = mycursor.fetchall()
    if myresultEmail:
        return "Email already exists", 400
    mycursor.execute("SELECT * FROM users WHERE PhoneNo = '" +
                     request.form['phone'] + "'")
    myresultPhone = mycursor.fetchall()
    if myresultPhone:
        return "Phone number already exists", 400
    Id = hashlib.sha256(
        (request.form['email'] + request.form['phone']).encode()).hexdigest()
    sql = "INSERT INTO users (UserType, Name, Password, PhoneNo, EmailID, UserID, Preferences, PFPnum) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    preferences = {'location': "", "skill": "", "income": ""}
    val = ('Contractor', request.form['name'], request.form['password'],
           request.form['phone'], request.form['email'], Id,
           json.dumps(preferences), str(randint(1, 5)))
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/PostRegisterLabourer', methods=['POST'])
def RegisterLabourer():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM users WHERE PhoneNo = '" +
                     request.form['phone'] + "'")
    myresultPhone = mycursor.fetchall()
    if myresultPhone:
        return "Phone number already exists", 400
    Id = hashlib.sha256((request.form['phone']).encode()).hexdigest()
    Preferences = {
        "location": "",
        "lat": "",
        "long": "",
        "skill": "",
        "income": "",
    }
    sql = "INSERT INTO users (UserType, Name, Password, PhoneNo, EmailID, UserID, Preferences, PFPnum) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    val = ('Labourer', request.form['name'], request.form['password'],
           request.form['phone'], "noEmail", Id, json.dumps(Preferences), str(randint(1, 5)))
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/PostLoginLabourer', methods=['POST'])
def LoginLabourer():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT UserID FROM users WHERE PhoneNo = '" +
                     request.form['phone'] + "' AND Password='" +
                     request.form['password'] + "' AND userType = 'Labourer'")
    myresultEmail = mycursor.fetchall()
    if not myresultEmail:
        return "Invalid account details", 400
    LoginId = hashlib.sha256(myresultEmail[0][0].encode()).hexdigest()
    sql2 = "INSERT INTO loginid (LoginID,temp) VALUES (%s, %s)"
    val2 = (LoginId, "temp")
    toBeReturned = []
    toBeReturned.append(myresultEmail[0][0])
    mycursor.execute(sql2, val2)
    mydb.commit()
    toBeReturned.append(LoginId)
    return json.dumps(toBeReturned), 200


@app.route('/PostLoginContractor', methods=['POST'])
def ContractorLabourer():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT UserID FROM users WHERE EmailID = '" +
                     request.form['email'] + "' AND Password='" +
                     request.form['password'] + "' AND userType = 'Contractor'")
    myresultEmail = mycursor.fetchall()
    if not myresultEmail:
        return "Invalid account details", 400
    LoginId = hashlib.sha256(myresultEmail[0][0].encode()).hexdigest()
    sql2 = "INSERT INTO loginid (LoginID,temp) VALUES (%s, %s)"
    val2 = (LoginId, "temp")
    toBeReturned = []
    toBeReturned.append(myresultEmail[0][0])
    mycursor.execute(sql2, val2)
    mydb.commit()
    toBeReturned.append(LoginId)
    return json.dumps(toBeReturned), 200


@app.route('/ChangeLocation', methods=['POST'])
def ChangeLocation():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Preferences FROM users WHERE UserID = '" +
                     request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    data = json.loads(myresult[0][0])
    dataToBeAdded = {
        "location": "",
        "lat": "",
        "long": "",
        "skill": "",
        "income": "",
    }
    dataToBeAdded['location'] = request.form['location']
    dataToBeAdded['lat'] = request.form['lat']
    dataToBeAdded['long'] = request.form['long']
    dataToBeAdded['skill'] = data['skill']
    dataToBeAdded['income'] = data['income']
    dataToBeAdded = json.dumps(dataToBeAdded)
    sql = "UPDATE users SET Preferences=%s WHERE UserID=%s"
    val = (dataToBeAdded, request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/ChangeSkill', methods=['POST'])
def ChangeSkill():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Preferences FROM users WHERE UserID = '" +
                     request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    data = json.loads(myresult[0][0])
    dataToBeAdded = {
        "location": "",
        "lat": "",
        "long": "",
        "skill": "",
        "income": "",
    }
    dataToBeAdded['location'] = data['location']
    dataToBeAdded['lat'] = data['lat']
    dataToBeAdded['long'] = data['long']
    dataToBeAdded['skill'] = request.form['skill']
    dataToBeAdded['income'] = data['income']
    dataToBeAdded = json.dumps(dataToBeAdded)
    sql = "UPDATE users SET Preferences=%s WHERE UserID=%s"
    val = (dataToBeAdded, request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/ChangeIncome', methods=['POST'])
def ChangeIncome():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Preferences FROM users WHERE UserID = '" +
                     request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    data = json.loads(myresult[0][0])
    dataToBeAdded = {
        "location": "",
        "lat": "",
        "long": "",
        "skill": "",
        "income": "",
    }
    dataToBeAdded['location'] = data['location']
    dataToBeAdded['lat'] = data['lat']
    dataToBeAdded['long'] = data['long']
    dataToBeAdded['skill'] = data['skill']
    dataToBeAdded['income'] = request.form['income']
    dataToBeAdded = json.dumps(dataToBeAdded)
    sql = "UPDATE users SET Preferences=%s WHERE UserID=%s"
    val = (dataToBeAdded, request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/ChangePhone', methods=['POST'])
def ChangePhone():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    sql = "UPDATE users SET PhoneNo=%s WHERE UserID=%s"
    val = (request.form['phone'], request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/ValidateLoginCookie', methods=['POST'])
def ValidateLoginCookie():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT LoginID FROM loginid WHERE LoginID = '" +
                     request.form['loginid'] + "'")
    myresult = mycursor.fetchall()
    if not myresult:
        return "Invalid Login Cookie"
    return "Valid Cookie"


@app.route('/GetPosts')
def GetPosts():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM posts")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/GetComments/<id>')
def GetComments(id):
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Details FROM comments WHERE PostID = '" + id + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/GetPostWithId/<id>')
def GetPostWithId(id):
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Details FROM posts WHERE PostID = '" + id + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/CreatePost', methods=['POST'])
def AddPost():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Name FROM users WHERE UserID = '" +
                     request.form['id'] + "'")
    myresult = mycursor.fetchall()
    Details = {
        "CreatorName": myresult[0][0],
        "CreatorID": request.form['id'],
        "content": request.form['content'],
        "IsVerified": "0",
    }
    PostID = hashlib.sha256((request.form['id'] + request.form['content']).encode()).hexdigest()
    sql = "INSERT INTO posts (PostID, Details) VALUES (%s, %s)"
    val = (PostID, json.dumps(Details))
    mycursor.execute(sql, val)
    mydb.commit()
    return "success", 200


@app.route('/AddComment', methods=['POST'])
def AddComment():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Name FROM users WHERE UserID = '" +
                     request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    Details = {
        "CreatorName": myresult[0][0],
        "CreatorID": request.form['userid'],
        "content": request.form['content'],
    }
    sql = "INSERT INTO comments (PostID, Details) VALUES (%s, %s)"
    val = (request.form['postid'], json.dumps(Details))
    mycursor.execute(sql, val)
    mydb.commit()
    return "success", 200


@app.route('/GetUserData/<id>')
def GetUserData(id):
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT userType, Name,Password,  EmailID, PhoneNO, Preferences FROM users WHERE UserID = '"
        + id + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult[0])


@app.route('/AdminLogin', methods=['POST'])
def AminLogin():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT UserID FROM admins WHERE Username = '" +
                     request.form['username'] + "' AND Password='" +
                     request.form['password'] + "'")
    myresultEmail = mycursor.fetchall()
    if not myresultEmail:
        return "Invalid account details", 400
    return myresultEmail[0][0], 200


@app.route('/AddDonation', methods=['POST'])
def AddDonation():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    DonationID = hashlib.sha256(
        (request.form['id'] + request.form['description'] + request.form['title']).encode()).hexdigest()
    sql = "INSERT INTO donations (Title, Description, Type, Target, Current, DonationID) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (
    request.form['title'], request.form['description'], request.form['type'], request.form['target'], "0", DonationID)
    mycursor.execute(sql, val)
    mydb.commit()
    return "success", 200


@app.route('/GetDonations')
def GetDonations():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM donations")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/GetJobs', methods=['POST'])
def GetJobs():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM jobs")
    result = []
    myresult = mycursor.fetchall()
    for x in myresult:
        print(x[2])
        Location = json.loads(x[2])
        dist = mpu.haversine_distance((float(request.form['lat']), float(request.form['long'])),
                                      (float(Location['lat']), float(Location['long'])))
        if (dist <= int(request.form['radius'])):
            result.append(json.dumps(x))
    return json.dumps(result)

@app.route('/GetJobsAll')
def GetJobsAll():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM jobs")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/GetJobsWithId/<id>')
def GetJobsWithId(id):
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM jobs WHERE JobID = '" + id + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/UpdateDonations', methods=['POST'])
def UpdateDonations():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Current FROM donations WHERE DonationID = '" +
                     request.form['id'] + "'")
    myresult = mycursor.fetchall()
    sql = "UPDATE donations SET Current=%s WHERE DonationID=%s"
    bal = str(int(myresult[0][0]) + int(request.form['value']))
    val = (bal, request.form['id'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/AddJob', methods=['POST'])
def AddJob():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT Name FROM users WHERE UserID = '" +
                     request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    sql = "INSERT INTO jobs (Title, Description, Location, Days, Pay,  JobID, Name, UserID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    Location = {
        "location": request.form['location'],
        "lat": request.form['lat'],
        "long": request.form['long'],

    }
    Id = hashlib.sha256(((request.form['id']) + request.form['desc'] + request.form['title']).encode()).hexdigest()
    print(request.form['userid'])
    val = (
    request.form['title'], request.form['desc'], json.dumps(Location), request.form['days'], request.form['pay'], Id,
    myresult[0][0], request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return "success", 200


@app.route('/AddJobP', methods=['POST'])
def AddJobP():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    sql = "INSERT INTO jobp (UserID, Status, JobID, CreatorID, Name, JobName, CreatorName) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    mycursor.execute("SELECT Name FROM users WHERE UserID = '" + request.form['userid'] + "'")
    myresult = mycursor.fetchall()
    mycursor.execute("SELECT Title FROM jobs WHERE JobID = '" + request.form['jobid'] + "'")
    myresult2 = mycursor.fetchall()
    mycursor.execute("SELECT Name FROM users WHERE UserID = '" + request.form['cid'] + "'")
    myresult3 = mycursor.fetchall()
    val = (request.form['userid'], "0", request.form['jobid'], request.form['cid'], myresult[0][0], myresult2[0][0],
           myresult3[0][0])
    mycursor.execute(sql, val)
    mydb.commit()
    return "success", 200


@app.route('/CheckIfApplied', methods=['POST'])
def CheckIfApplied():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT Status FROM jobp WHERE JobID = '" + request.form['jobid'] + "' AND UserID = '" + request.form[
            'userid'] + "'")
    myresult = mycursor.fetchall()
    if not myresult:
        return "false"
    return "true"


@app.route('/GetJobCreator', methods=['POST'])
def GetJobCreator():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT UserID FROM jobs WHERE JobID = '" + request.form['jobid'] + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/ContractJobUpdates', methods=['POST'])
def ContractJobUpdates():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT JobID, UserID, Status, Name, JobName FROM jobp WHERE CreatorID = '" + request.form['cid'] + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


@app.route('/UpdateJob', methods=['POST'])
def UpdateJob():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    sql = "UPDATE jobp SET Status=%s WHERE JobID=%s AND UserID=%s"
    val = ("1", request.form['jobid'], request.form['userid'])
    mycursor.execute(sql, val)
    mydb.commit()
    return 'success', 200


@app.route('/LabourerJobUpdates', methods=['POST'])
def LabourerJobUpdates():
    mydb = mysql.connector.connect(host=os.environ['host'],
                                   user=os.environ['user'],
                                   password=os.environ['pass'],
                                   database=os.environ['db'])
    mycursor = mydb.cursor()
    mycursor.execute("SELECT JobID, Status,JobName, CreatorName, CreatorID FROM jobp WHERE UserID = '" + request.form[
        'userid'] + "'")
    myresult = mycursor.fetchall()
    return json.dumps(myresult)


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5002)
    # serve(app, host='127.0.0.1', port=5003)
    serve(app, host='0.0.0.0', port=5000)
    # app.run(debug=True)