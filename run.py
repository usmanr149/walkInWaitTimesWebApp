from flask import Flask, render_template, request, jsonify

from getHospitalData import getHospitalWaitTimes, getHTML, fixValue
from getMedicentreData import getMedicentreData, find_word, getMedicentreHTML
from getOtherClinicsData import getOtherClinicsHTML
from getRecommendation import getRecommendation

import re, datetime

import configparser

config = configparser.ConfigParser()
config.read("./.properties")

api = config['SECTION_HEADER']['api']
host = config['SECTION_HEADER']['host']
port = config['SECTION_HEADER']['port']

app = Flask(__name__)

#this function get the hospital wait time table
@app.route('/hospitalWaitTimes')
def updateTimes(url="http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"):
    hospital_wait_times, time = getHospitalWaitTimes()
    table = getHTML(hospital_wait_times, time)
    return jsonify(table=table)

#this function hosts the medicentre data table, it is updated by medicentreWaitTimes
@app.route('/updateMedicentreWaitTimes')
def updateMedicentreWaitTimes():
    soup = getMedicentreData()

    medicenter_wait_times = {}

    for elem in soup.select('div.col-sm-12.medicentre'):
        if "Edmonton," in elem.find(class_='address').get_text() \
                or 'Sherwood Park' in elem.find(class_='address').get_text() \
                or 'St. Albert' in elem.find(class_='address').get_text():
            name = elem.find('a').get_text()
            s1 = re.findall(r'\d+', elem.find(class_='waittime').get_text())

            waitTimes = {}
            for t in s1[:-2]:
                waitTimes[elem.find(class_='waittime').get_text().split(" ")[elem.find(class_=
                                                                                       'waittime').get_text().split(" ")
                                                                                 .index(t) + 1]] = t
            if len(s1) > 1:
                lastUpdated = str(s1[-2]) + ":" + str(s1[-1])
                if find_word(elem.find(class_='waittime').get_text(), 'am'):
                    lastUpdated += ' am'
                else:
                    lastUpdated += ' pm'

            else:
                lastUpdated = "Clinic Closed"

            hr_min = lambda y, x: y[x] if x in y.keys() else "00"
            medicenter_wait_times[name.split(" ")[0] + "_update_time"] = """<div class="radiotext" style="text-align: center;">
            <label id="{0}_time" for="regular" data-wait_hr="{1}" 
            data-wait_min="{2}" >{1} hr {2} min</label></div>
            <div class="radiotext" style="text-align: center;">(last updated: {3})</div>""".format(name.split(" ")[0],
                                                                                                   hr_min(waitTimes, 'hr'),
                                                                                                   hr_min(waitTimes, 'mins'),
                                                                                                   lastUpdated).replace("\n", "")

    return jsonify(result=medicenter_wait_times)

#need a webpage that hosts the up-to-date medicentre Wait Times
@app.route('/medicentreWaitTimes')
def medicentreWaitTimes():
    medicentreWaitTimes_ = getMedicentreHTML()
    return jsonify(table=medicentreWaitTimes_)

#this page hosts the data for other clinics
@app.route('/otherClinics')
def otherClinics():
    return jsonify(table=getOtherClinicsHTML())

@app.route('/updateHospitalWaitTimes')
def updateHospitalWaitTimes(url="http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"):
    hospital_wait_times, now_time = getHospitalWaitTimes()
    keys = [k for k in hospital_wait_times.keys()]
    for k in keys:
        hospital_wait_times[k] = hospital_wait_times[k][:2] + ":" + hospital_wait_times[k][2:]
        hospital_wait_times[fixValue(k)[0].split(" ")[0] + "_time"] = hospital_wait_times.pop(k)
    hospital_wait_times['update_time'] = str(now_time[:4]) + " " + str(now_time[4:])
    return jsonify(result=hospital_wait_times)

@app.route('/recommend')
def recommend():
    origin = request.args.get('origin', 0, type=str)
    mode = request.args.get('mode',0,type=str)
    bestTime, where, type = getRecommendation(origin, mode)
    if bestTime != None:
        bestTime = datetime.datetime.fromtimestamp(bestTime / 1000).strftime('%Y-%m-%d %H:%M %p')
    return jsonify(where=where, type=type, bestTime=bestTime)

@app.route('/')
def index():
    return "Hello World"
    #hospital_wait_times, time = getHospitalWaitTimes()
    #table = getHTML(hospital_wait_times, time)
    #return render_template("view.html", table=table, api=api)

@app.route('/view')
def view():
    hospital_wait_times, time = getHospitalWaitTimes()
    table = getHTML(hospital_wait_times, time)
    return render_template("view.html", table=table, api=api)


if __name__ == '__main__':
    app.run(debug=True, host=host,port=int(port), threaded=True)