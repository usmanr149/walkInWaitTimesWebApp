import geocoder, json, re
import pandas as pd

import requests
import urllib

import datetime

from bs4 import BeautifulSoup
from getMedicentreData import getAvgMedicentreWaitTimes
from getOtherClinicsData import twelveto24

import configparser

config = configparser.ConfigParser()
config.read("./.properties")

host = config['SECTION_HEADER']['host']
port = config['SECTION_HEADER']['port']
port2 = "162.106.216.28"

def readAddresses():
    df = pd.read_csv("static/data/addresses.csv")
    return df.set_index('address').T.to_dict('list')

#get wait time in milliseconds to add to the unix timestamp
def getMedicentreWaitTime(loc, medicentre_response):
    key = loc.split(" ")[0]
    r = BeautifulSoup(medicentre_response['result']['{0}_update_time'.format(key)], "lxml")
    wait_hour = float(r.find(id="{0}_time".format(key)).get("data-wait_hr"))
    wait_min = float(r.find(id="{0}_time".format(key)).get("data-wait_min"))
    return wait_hour*3600*1000+wait_min*60*1000

#check if it is reasonable to go to a medicentre right now and arrive 10 minute before it closes
def checkMedicentreOpenCloseTime(arrTime, medicentre):
    dow = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    day = dow[datetime.datetime.today().weekday()]

    df = pd.read_csv("static/data/MedicentreTimes.csv")
    try:
        close = float(df[(df["Medicentre Name"] == medicentre) & (df["Day"] == day)]["Close"].iloc[0])
        open_ = float(df[(df["Medicentre Name"] == medicentre) & (df["Day"] == day)]["Open"].iloc[0])

        if datetime.datetime.fromtimestamp(int((arrTime)/1000)).hour + datetime.datetime.fromtimestamp(int((arrTime)/1000)).minute/60 > open_ and \
                        datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).hour + \
                                        datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).minute/60 < close:
            return True
        else:
            return False
    except IndexError:
        return False


#check if it is reasonable to go to a walk-in clinic
def checkWalInClinicOpenClose(arrTime, clinic):
    #print(datetime.datetime.fromtimestamp(int((arrTime) / 1000)).strftime('%H:%M'))
    with open('static/data/clinicLocationTimes.json', 'r') as fp:
        clinicLocationTimes = json.load(fp)

    dow = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday', 'h': 'Holiday'}
    todayDOW = dow[datetime.datetime.today().weekday()]

    days = clinicLocationTimes[clinic]['Hours']
    for day in days:
        if todayDOW in day:
            times = re.findall(r'\d{1,2}:\d{1,2} (?:AM|PM)', day)
            #this means the clinic doesn't do breaks
            if len(times) == 2:
                times = [twelveto24(x) for x in times]
                open_ = float(times[0].split(":")[0])+float(times[0].split(":")[1])/60
                close = float(times[1].split(":")[0])+float(times[1].split(":")[1])/60
                #check that the clinic is open
                if datetime.datetime.fromtimestamp(int((arrTime) / 1000)).hour + datetime.datetime.fromtimestamp(int((arrTime) / 1000)).minute/60 > open_ and \
                                datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).hour + \
                                        datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).minute/60 < close:
                    return True
                else:
                    return False
            if len(times) == 4:
                times = [twelveto24(x) for x in times]
                open_ = float(times[0].split(":")[0])+float(times[0].split(":")[1])/60
                breakOpen = float(times[1].split(":")[0])+float(times[1].split(":")[1])/60
                breakClose = float(times[2].split(":")[0])+float(times[2].split(":")[1])/60
                close = float(times[3].split(":")[0])+float(times[3].split(":")[1])/60
                #check you don't arrive druring break
                if datetime.datetime.fromtimestamp(int((arrTime) / 1000)).hour + datetime.datetime.fromtimestamp(int((arrTime) / 1000)).minute/60 >= breakOpen and \
                                datetime.datetime.fromtimestamp(int((arrTime) / 1000)).hour + datetime.datetime.fromtimestamp(int((arrTime) / 1000)).minute <= breakClose:
                    return False
                #if not on a break then check it is open and not close to closing
                elif datetime.datetime.fromtimestamp(int((arrTime) / 1000)).hour + datetime.datetime.fromtimestamp(int((arrTime) / 1000)).minute/60 > open_ and \
                                datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).hour + \
                                        datetime.datetime.fromtimestamp(int((arrTime + 15 * 60 * 1000) / 1000)).minute/60 < close:
                    return True
                else:
                    return False
    return False


#get wait time in milliseconds to add to the unix timestamp
#hospitals are open at all time
def getHospitalWaitTimes(loc, hospital_response):
    key = loc.split(" ")[0]
    wait_hour = float(hospital_response['result']["{0}_time".format(key)].split(":")[0])
    wait_min = float(hospital_response['result']["{0}_time".format(key)].split(":")[1])
    return wait_hour*3600*1000+wait_min*60*1000


def getRecommendation(address, mode='TRANSIT'):
    print(address)

    if mode=='TRANSIT':
        mode = "TRANSIT,WALK"


    try:
        if isinstance(float(address.split(",")[0]), float) and isinstance(float(address.split(",")[1]), float):
            correctAddress = True
            add = [float(address.split(",")[0]), float(address.split(",")[1])]
    except:
        g = geocoder.google(address)
        if isinstance(g.latlng, list) and len(g.latlng) > 1:
            correctAddress = True
            add = [g.latlng[0], g.latlng[1]]

    print(add)
    print(mode)
    bestTime = None
    recomendation = None
    typeofrecommendation = None

    #make sure the google address yields a result
    if correctAddress:
        #read in the current medicentre wait times
        medicentre_response = requests.get("http://"+host+":"+port+"/updateMedicentreWaitTimes").json()
        #get the current hospital wait times
        hospital_response = requests.get("http://" + host + ":" + port + "/updateHospitalWaitTimes").json()
        #get the estimated wait times for other walk-in clinics, the response is in seconds
        otherClinicsWaitTimes = getAvgMedicentreWaitTimes(format="seconds")

        time_ = datetime.datetime.now()
        for k, v in readAddresses().items():

            url = """http://{5}:8080/otp/routers/default/plan?fromPlace={0}&toPlace={1}&time={2}&date={3}&mode={4}&maxWalkDistance=804.672&arriveBy=false&wheelchair=false&locale=en""".format(
                urllib.parse.quote(str(add[0]) + "," + str(add[1])),
                urllib.parse.quote(str(v[0]) + "," + str(v[1])),
                urllib.parse.quote(time_.strftime("%I:%M%p")),
                urllib.parse.quote(time_.strftime("%m-%d-%Y")),
                mode, port2)
            print(url)
            try:
                response = requests.get(url).json()
                #the response is the unix timestamp in milliseconds
                arrTime = float(response["plan"]["itineraries"][0]["endTime"])
                if "Hospital" in k:
                    arrTime += getHospitalWaitTimes(k, hospital_response)
                    #print('hospital = ', k)
                    #print("waitTime = ", getHospitalWaitTimes(k, hospital_response))
                    # print(arrTime)
                    #print("Estimated time to being seen: ", datetime.datetime.fromtimestamp(arrTime/1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    #print("-------------------")
                    if bestTime == None or arrTime < bestTime:
                        bestTime = arrTime
                        recomendation = k
                        typeofrecommendation = 'hospitals'
                elif "Medicentre" in k:
                    # make sure the patient doesn't arrive during a break or when the clinic is closed or near closing
                    # (i.e. arrive atleast fifteen before closing time)
                    arrTime += getMedicentreWaitTime(k, medicentre_response)
                    #print("medicentre = ", k)
                    #print("waitTime = ", getMedicentreWaitTime(k, medicentre_response))
                    #print("Estimated time to being seen: ", datetime.datetime.fromtimestamp(arrTime / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    # print(checkMedicentreOpenCloseTime(arrTime, k))
                    #print("-------------------")
                    if checkMedicentreOpenCloseTime(arrTime, k):
                        if bestTime == None or arrTime < bestTime:
                            bestTime = arrTime
                            recomendation = k
                            typeofrecommendation = 'medicentres'
                else:
                    #add a 10 minute buffer time because we don't know the wait time of the walk-in clinics
                    arrTime += otherClinicsWaitTimes*1000 + 10*60*1000
                    #print('other = ', k)
                    # print(arrTime)
                    #print("Estimated time to being seen: ", datetime.datetime.fromtimestamp(arrTime / 1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
                    # print(checkWalInClinicOpenClose(arrTime, k))
                    #print("-------------------")
                    if checkWalInClinicOpenClose(arrTime, k):
                        if bestTime == None or arrTime < bestTime:
                            bestTime = arrTime
                            recomendation = k
                            typeofrecommendation = 'other'
            except KeyError:
                pass
                # print("PATH_NOT_FOUND")

        return bestTime, recomendation, typeofrecommendation
    return bestTime, recomendation, typeofrecommendation


if __name__ == "__main__":
    print(getRecommendation("53.5526619,-113.488818"))
    #print(getRecommendation("Century Place, Edmonton"))
    #medicentre_response = requests.get("http://" + host + ":" + port + "/updateMedicentreWaitTimes").json()
    #print(getMedicentreWaitTime("Kingsway Medicentre", medicentre_response))