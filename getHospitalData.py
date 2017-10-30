from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests, json, re, time

#import geocoder

import configparser, datetime

config = configparser.ConfigParser()
config.read("./.properties")

host = config['SECTION_HEADER']['host']
port = config['SECTION_HEADER']['port']


def getHospitalWaitTimes():
    url = "http://www12.albertahealthservices.ca/repacPublic/SnapShotController?direct=displayEdmonton"
    page = urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    now_time = soup.find_all("div", class_="publicRepacDate")[0].findAll(text=True)[1].replace("\n", "").replace("\r",
                                                                                                                 "").replace(
        " ", "")
    hospital_wait_times = {}
    for hit in soup.find_all("tr"):
        if len(hit.find_all("td", class_="publicRepacSiteCell")) > 0:
            time = ''
            # print(hit.find("td", class_="publicRepacSiteCell").text)
            for img in hit.find_all("img", attrs={"alt": True}):
                # print(img.get("alt"))
                time += img.get("alt")
            hospital_wait_times[hit.find("td", class_="publicRepacSiteCell").text] = time

    return hospital_wait_times, now_time

#fix hospital name
def fixValue(key):
    s = [i.strip() for i in key.splitlines() if len(i.strip()) > 0]
    return s


def getHTML(data, updateTime):

    html = ["<table class='table table-responsive' "
                                                     "style='width: 478.4px; padding-left: 5px;'><thead><tr>"
            "<th style='width:  293px; text-align: center;'><span style='color: #ff0000;'>Hospital</span></th>"
            "<th style='width: 175.4px; text-align: center;'><span style='color: #ff0000;'><br />Wait Times<br />Updated at <p style='display:inline' id = 'update_time'>{0}</p></span></th>"
                "</tr></thead><tbody>".format(str(updateTime[:4]) + " " + str(updateTime[4:]))]
    for key, value in data.items():
        k = fixValue(key)
        html.append("<tr>")
        html.append("<td>")
        html.append("<div class ='radio'>")
        if len(k) > 1:
            html.append("<label> <input type = 'radio' id = 'location_hospital_{0}' name = 'optradio' value = {1},Edmonton>".format(
                k[0].split(" ")[0],  k[0].replace(" ", "+")))
            html.append("{0}</label>".format(k[0]))
            html.append('<div class="add_info"><span style="color: #ff0000;"><label>{0}</label></span></div>'.format(k[1]))
        else:
            html.append("<label> <input type = 'radio' id = 'location_hospital_{0}' name = 'optradio' value = {1},Edmonton>".format(
                k[0].split(" ")[0], k[0].replace(" ", "+")))
            html.append("{0}</label>".format(k[0]))

        html.append("</div>")
        html.append("</td><td><div class ='radiotext' style='text-align: center;'>")
        html.append("<label for='regular' id = '{1}_time'>{0}</label>".format(str(value[:2])+":"+str(value[2:]), k[0].split(" ")[0]))
        html.append("</div></td></tr>")

    html.append("</table>")

    return "\n".join(html)