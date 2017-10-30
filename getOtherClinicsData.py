import requests, json, re, time

#import geocoder

from getMedicentreData import getAvgMedicentreWaitTimes

import configparser, datetime

config = configparser.ConfigParser()
config.read("./.properties")

host = config['SECTION_HEADER']['host']
port = config['SECTION_HEADER']['port']


def getCurrentStatus(openTime, closeTime, breakOpenTime=None, breakCloseTime=None):
    if breakOpenTime != None and breakCloseTime != None:
        breakCloseTime_ = float(breakCloseTime.split(":")[0]) + float(breakCloseTime.split(":")[1])/60
        breakOpenTime_ = float(breakOpenTime.split(":")[0]) + float(breakOpenTime.split(":")[1])/60
        if datetime.datetime.now().hour + datetime.datetime.now().minute/60 >= breakOpenTime_ \
        and datetime.datetime.now().hour + datetime.datetime.now().minute/60 <= breakCloseTime_:
            return "On Break"
        elif datetime.datetime.now().hour + datetime.datetime.now().minute/60 >= float(closeTime.split(":")[0]) + float(closeTime.split(":")[1])/60 \
        or datetime.datetime.now().hour + datetime.datetime.now().minute/60 <= float(openTime.split(":")[0]) + float(openTime.split(":")[1])/60:
            return "Clinic Closed"
        else:
            return "Open till {0}".format(closeTime)
    else:
        closeTime_ = float(closeTime.split(":")[0]) + float(closeTime.split(":")[1])/60
        openTime_ = float(openTime.split(":")[0]) + float(openTime.split(":")[1])/60
        if datetime.datetime.now().hour + datetime.datetime.now().minute/60 >= closeTime_ \
        or datetime.datetime.now().hour + datetime.datetime.now().minute/60 <= openTime_:
            return "Clinic Closed"
        else:
            return "Open till {0}".format(closeTime)

def twelveto24(time):
    if "AM" in time:
        t = time.replace("AM", "").strip().split(":")
        return str(int(t[0])%12) + ":" + str(t[1])
    elif "PM" in time:
        t = time.replace("PM", "").strip().split(":")
        return str(int(float(t[0])%12+12)) + ":" + str(t[1])


def getOtherClinicsHTML(url='http://www.walkinhealth.ca/directory/walk-in-clinic/ab/edmonton/'):
    with open('static/data/clinicLocationTimes.json', 'r') as fp:
        clinicLocationTimes = json.load(fp)

    dow = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday', 'h': 'Holiday'}
    todayDOW = dow[datetime.datetime.today().weekday()]

    html = ["""<table class="table table-responsive" style="width: 478.4px; float: left;">
        <thead>
        <tr>
        <th style="width: 293px; text-align: center;"><span style="color: #ff0000;"><strong>Name</strong></span></th>
        <th style="width: 175.4px;">
        <p><span style="color: #ff0000;"><strong>Hours Open Today</strong></span></p>
        <div class="\&quot;radiotext\&quot;" style="text-align: center;" id="EstimatedWaitTime"><p>Estimated Wait Time:</p><p>{0}</p></div>
        </th>
        </tr>
        </thead>
        <tbody>"""]
    for k, v in clinicLocationTimes.items():
        if 'Medicentre' not in k:
            for day in v['Hours']:
                if todayDOW in day:
                    times = re.findall(r'\d{1,2}:\d{1,2} (?:AM|PM)', day)
                    if len(times) == 2:
                        html.append("""<tr>
                            <td>
                            <div class="radio"><label> <input id="location_{0}" name="optradio" type="radio" value="{1}" />{2}</label></div>
                            </td>
                            <td>
                            <div class="radiotext" style="text-align data-open_time="{4}" data-close_time="{5}": center;">{3}</div>
                            </td>
                            </tr>""".format(k.split(" ")[0], v['location'].replace(" ", "+"), k,
                                            getCurrentStatus(openTime=twelveto24(times[0]), closeTime=twelveto24(times[1])),
                                            twelveto24(times[0]), twelveto24(times[1])))
                    elif len(times) == 4:
                        html.append("""<tr>
                            <td>
                            <div class="radio"><label> <input id="location_{0}" name="optradio" type="radio" value="{1}" />{2}</label></div>
                            </td>
                            <td>
                            <div class="radiotext" style="text-align data-open_time="{4}" data-break_open="{5}" data-break_close="{6}" data-close_time="{7}": center;">{3}</div>
                            </td>
                            </tr>""".format(k.split(" ")[0], v['location'].replace(" ", "+"), k,
                                            getCurrentStatus(openTime=twelveto24(times[0]),
                                                             closeTime=twelveto24(times[3]),
                                                             breakOpenTime=twelveto24(times[1]),
                                                             breakCloseTime=twelveto24(times[2])),
                                            twelveto24(times[0]), twelveto24(times[1]), twelveto24(times[2]),
                                            twelveto24(times[3])))
                    break
    html.append("""</tbody></table>""")
    avgWaitTime = getAvgMedicentreWaitTimes()
    return "".join(html).replace("\n", "").format(avgWaitTime)

if __name__ ==  "__main__":
    print(getCurrentStatus("8:00", "14:00"))