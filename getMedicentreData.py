from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests, json, re, time

#import geocoder

import configparser, datetime

config = configparser.ConfigParser()
config.read("./.properties")

host = config['SECTION_HEADER']['host']
port = config['SECTION_HEADER']['port']



def getMedicentreData(url= "https://www.medicentres.com/clinic-locations/"):
    payload = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
               "Accept-Encoding": "gzip, deflate, br",
               "Accept-Language": "en-GB,en-US;q=0.8,en;q=0.6",
               "Cache-Control": "max-age=0",
               "Connection": "keep-alive",
               "Content-Length": "103",
               "Content-Type": "application/x-www-form-urlencoded",
               "Cookie": "_ga=GA1.2.1572985675.1506014656; _gid=GA1.2.297042775.1507133010",
               "Host": "www.medicentres.com",
               "Origin": "https://www.medicentres.com",
               "Referer": "https://www.medicentres.com/clinic-locations/",
               "Upgrade-Insecure-Requests": "1",
               "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
               }
    data = {"navigator": "yes",
            "city": "Edmonton, Alberta",
            "clinic": "",
            "waittimes": "all",
            "distancewithin": "all",
            "waittimer-submit": "Submit"}
    r = requests.post(url=url, headers=payload, data=json.dumps(data))

    return BeautifulSoup(r.content, "lxml")


#get an estimate for the waitTimes at the walk-in Clinics
def getAvgMedicentreWaitTimes(url = "http://" + host + ":" + port + "/updateMedicentreWaitTimes"):
    # get an estimate of the wait times for the other clinics by averaging the wait times of the medicentre clinic
    medicentre_response = requests.get("http://" + host + ":" + port + "/updateMedicentreWaitTimes").json()
    i = 0
    waitTimes = 0
    for k, v in medicentre_response['result'].items():
        r = BeautifulSoup(v, 'lxml')
        waitTimes += float(r.find(id="{0}_time".format(k.split("_")[0])).get("data-wait_hr")) + \
                     float(r.find(id="{0}_time".format(k.split("_")[0])).get("data-wait_min")) / 60
        i += 1

    avgWaitTime = waitTimes/i

    if int(avgWaitTime) > 0 and int((avgWaitTime - int(avgWaitTime))*60) > 10:
        formatAvgWaitTimes = str(int(avgWaitTime)) + " hr " + str(int((avgWaitTime - int(avgWaitTime))*60)) + " min"
    else:
        formatAvgWaitTimes = "00 hr and 10 min"
    return formatAvgWaitTimes

def find_word(text, search):
    result = re.findall('\\b' + search + '\\b', text, flags=re.IGNORECASE)
    if len(result) > 0:
        return True
    else:
        return False

def getMedicentreHTML(url= "https://www.medicentres.com/clinic-locations/"):

    soup = getMedicentreData()
    html = ["""<table style='padding-left: 5px;'>
        <tbody>
        <tr>
        <td style="text-align: center;"  width=60%;><span style="color: #ff0000;">
        <strong>Medicentre</strong></span></td>
        <td style="text-align: center;">
        <span style="color: #ff0000;" width=40%> <strong>Wait Time</strong>
        </span></td></tr><tr>"""]
    for elem in soup.select('div.col-sm-12.medicentre'):
        if "Edmonton," in elem.find(class_='address').get_text() \
                or 'Sherwood Park' in elem.find(class_='address').get_text() \
                or 'St. Albert' in elem.find(class_='address').get_text():
            name = elem.find('a').get_text()
            add = elem.find(class_='address').get_text()
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
                hr_min = lambda y, x: y[x] if x in y.keys() else "00"
                html.append("""<tr>
                            <td>
                            <div class="radio"><label> <input id="{0}"
                            name="optradio" type="radio" value="{1}"  />{2}</label></div>
                            </td>
                            <td id="{0}_update_time">
                            <div class="radiotext" style="text-align: center;">
                            <label id="{0}_time" for="regular" data-wait_hr="{3}" 
                            data-wait_min="{4}" >{3} hr {4} min</label></div>
                            <div class="radiotext" style="text-align: center;">(last updated: {5})</div>
                            </td>
                            </tr>
                            """.format(name.split(" ")[0], add.replace(" ", "+"), name, hr_min(waitTimes, 'hr'),
                                       hr_min(waitTimes, 'mins'), lastUpdated))

            else:
                lastUpdated = "Clinic Closed"
                html.append("""<tr>
                            <td>
                            <div class="radio"><label> <input id="{0}"
                            name="optradio" type="radio" value="{1}"  />{2}</label></div>
                            </td>
                            <td id="{0}_update_time">
                            <div class="radiotext" style="text-align: center;">
                            <label id="{0}_time" for="regular" data-wait_hr="0" 
                            data-wait_min="0" >Clinic Closed</label></div>
                            <div class="radiotext" style="text-align: center;">(last updated: {5})</div>
                            </td>
                            </tr>
                            """.format(name.split(" ")[0], add.replace(" ", "+"), name, 0,
                                       0, lastUpdated))

    html.append("""</tbody></table>""")

    return "".join(html)

#get an estimate for the waitTimes at the walk-in Clinics
def getAvgMedicentreWaitTimes(url = "http://" + host + ":" + port + "/updateMedicentreWaitTimes",format = 'html'):
    # get an estimate of the wait times for the other clinics by averaging the wait times of the medicentre clinic
    medicentre_response = requests.get("http://" + host + ":" + port + "/updateMedicentreWaitTimes").json()
    i = 0
    waitTimes = 0
    for k, v in medicentre_response['result'].items():
        r = BeautifulSoup(v, 'lxml')
        waitTimes += float(r.find(id="{0}_time".format(k.split("_")[0])).get("data-wait_hr")) + \
                     float(r.find(id="{0}_time".format(k.split("_")[0])).get("data-wait_min")) / 60
        i += 1

    avgWaitTime = waitTimes/i

    print(avgWaitTime)

    #this if to use the reponse for the getRecommendation function in seconds
    if format != 'html':
        return avgWaitTime*3600

    if int(avgWaitTime) > 0 or int((avgWaitTime - int(avgWaitTime))*60) > 10:
        formatAvgWaitTimes = str(int(avgWaitTime)) + " hr " + str(int((avgWaitTime - int(avgWaitTime))*60)) + " min"
    else:
        formatAvgWaitTimes = "00 hr and 10 min"
    return formatAvgWaitTimes


if __name__ == "__main__":
    print(getAvgMedicentreWaitTimes())