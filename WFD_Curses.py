#!/usr/bin/env python3

"""
COLOR_BLACK	    Black
COLOR_BLUE	    Blue
COLOR_CYAN	    Cyan (light greenish blue)
COLOR_GREEN	    Green
COLOR_MAGENTA	Magenta (purplish red)
COLOR_RED   	Red
COLOR_WHITE 	White
COLOR_YELLOW	Yellow
"""

import os
import logging
import datetime
from pathlib import Path
from bs4 import BeautifulSoup

if Path("./debug").exists():
    logging.basicConfig(
        filename="debug.log",
        filemode="w",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )
    logging.debug("Debug started")

cloudLogOn = False
qrzsession = False
hamdbOn = False
hamqthSession = False
pollTime = datetime.datetime.now()

try:
    import json
    import requests

    confFile = os.path.expanduser("~") + "/.config/wfd.ini"

    if os.path.exists(confFile):
        fd = open(confFile)
        try:
            confData = json.load(fd)
        except Exception as e:
            logging.debug(f"{e}")
        fd.close()
    elif os.path.exists("/usr/local/etc/wfd.ini"):
        fd = open("/usr/local/etc/wfd.ini")
        try:
            confData = json.load(fd)
        except Exception as e:
            logging.debug(f"{e}")
        fd.close()
    elif os.path.exists("/etc/wfd.ini"):
        fd = open("/etc/wfd.ini")
        try:
            confData = json.load(fd)
        except Exception as e:
            logging.debug(f"{e}")
        fd.close()

    if confData["cloudlog"]["enable"].lower() == "yes":

        cloudlogapi = confData["cloudlog"]["apikey"]
        cloudlogurl = confData["cloudlog"]["url"]

        payload = "/validate/key=" + cloudlogapi
        r = requests.get(cloudlogurl + payload)

        if r.status_code == 200 or r.status_code == 400:
            cloudLogOn = True

    if confData["qrz"]["enable"].lower() == "yes":

        qrzurl = confData["qrz"]["url"]
        qrzname = confData["qrz"]["username"]
        qrzpass = confData["qrz"]["password"]

        payload = {"username": qrzname, "password": qrzpass}
        r = requests.get(qrzurl, params=payload, timeout=1.0)

        if r.status_code == 200:
            xmlData = BeautifulSoup(r.text, "xml")
            if xmlData.QRZDatabase.Session.Key.string:
                qrzsession = xmlData.QRZDatabase.Session.Key.string
        else:
            qrzsession = False

    if confData["hamdb"]["enable"].lower() == "yes":
        hamdbOn = True

    if confData["hamqth"]["enable"].lower() == "yes":
        payload = {
            "u": confData["hamqth"]["username"],
            "p": confData["hamqth"]["password"],
        }
        r = requests.get(confData["hamqth"]["url"], params=payload)
        if r.status_code == 200:
            xmlData = BeautifulSoup(r.text, "xml")
            hamqthSession = xmlData.HamQTH.session.session_id.string
        else:
            hamqthSession = False

except:
    cloudlogapi = False
    cloudlogurl = False
    cloudLogOn = False
    HamDbOn = False
    qrz = False
    qrzsession = False
    hamqthSession = False

import curses
import time
import sqlite3
import socket
import re
import sys

from pathlib import Path
from curses.textpad import rectangle
from curses import wrapper
from sqlite3 import Error

stdscr = curses.initscr()
qsoew = 0
qso = []
quit = False

BackSpace = 263
Escape = 27
QuestionMark = 63
EnterKey = 10
Space = 32

modes = ("PH", "CW", "DI")
bands = (
    "160",
    "80",
    "60",
    "40",
    "30",
    "20",
    "17",
    "15",
    "12",
    "10",
    "6",
    "2",
    "222",
    "432",
)
dfreqPH = {
    "160": "1.910",
    "80": "3.800",
    "60": "5.357",
    "40": "7.200",
    "30": "10.135",
    "20": "14.200",
    "17": "18.150",
    "15": "21.400",
    "12": "24.950",
    "10": "28.400",
    "6": "53.000",
    "2": "146.520",
    "222": "223.500",
    "432": "446.000",
    "SAT": "0.0",
    "None": "0.0",
}
dfreqCW = {
    "160": "1.810",
    "80": "3.550",
    "60": "5.357",
    "40": "7.070",
    "30": "10.135",
    "20": "14.080",
    "17": "18.100",
    "15": "21.100",
    "12": "24.910",
    "10": "28.150",
    "6": "50.050",
    "2": "144.050",
    "222": "223.500",
    "432": "425.000",
}

validSections = [
    "CT",
    "RI",
    "EMA",
    "VT",
    "ME",
    "WMA",
    "NH",
    "ENY",
    "NN",
    "NLI",
    "SNJ",
    "NNJ",
    "WNY",
    "DE",
    "MDC",
    "EPA",
    "EPA",
    "AL",
    "SC",
    "GA",
    "SFL",
    "KY",
    "TN",
    "NC",
    "VA",
    "NFL",
    "VI",
    "PR",
    "WCF",
    "AR",
    "NTX",
    "LA",
    "OK",
    "MS",
    "STX",
    "NM",
    "WTX",
    "EB",
    "SCV",
    "LAX",
    "SDG",
    "ORG",
    "SF",
    "PAC",
    "SJV",
    "SB",
    "SV",
    "AK",
    "NV",
    "AZ",
    "OR",
    "EWA",
    "UT",
    "ID",
    "WWA",
    "MT",
    "WY",
    "MI",
    "WV",
    "OH",
    "IL",
    "WI",
    "IN",
    "CO",
    "MO",
    "IA",
    "ND",
    "KS",
    "NE",
    "MN",
    "SD",
    "AB",
    "NT",
    "BC",
    "ONE",
    "GTA",
    "ONN",
    "MAR",
    "ONS",
    "MB",
    "QC",
    "NL",
    "SK",
    "PE",
]

mycall = "YOURCALL"
myclass = "CLASS"
mysection = "SECT"
freq = "000000000"
power = "0"
band = "40"
mode = "CW"
qrp = False
highpower = False
bandmodemult = 0
altpower = False
outdoors = False
notathome = False
satellite = False
cwcontacts = "0"
phonecontacts = "0"
digitalcontacts = "0"
contacts = ""
contactsOffset = 0
logNumber = 0
kbuf = ""
editbuf = ""
maxFieldLength = [17, 5, 7, 20, 4, 3, 4]
maxEditFieldLength = [10, 17, 5, 4, 20, 4, 3, 4, 10]
inputFieldFocus = 0
editFieldFocus = 1
hiscall = ""
hissection = ""
hisclass = ""

database = "WFD_Curses.db"
conn = ""
wrkdsections = []
scp = []
secPartial = {}
secName = {}
secState = {}
oldfreq = "0"
oldmode = ""
oldpwr = 0
rigctrlhost = "localhost"
rigctrlport = 4532
rigonline = False


def reinithamqth():
    global confData
    payload = {"u": confData["hamqth"]["username"], "p": confData["hamqth"]["password"]}
    r = requests.get(confData["hamqth"]["url"], params=payload)
    if r.status_code == 200:
        xmlData = BeautifulSoup(r.text, "xml")
        hamqthSession = xmlData.HamQTH.session.session_id.string
    else:
        hamqthSession = False
    return hamqthSession


def reinitqrz():
    global confData
    payload = {"u": confData["qrz"]["username"], "p": confData["qrz"]["password"]}
    r = requests.get(confData["qrz"]["url"], params=payload)
    if r.status_code == 200:
        xmlData = BeautifulSoup(r.text, "xml")
        qrzsession = xmlData.QRZDatabase.Session.Key.string
    else:
        qrzsession = ""
    return qrzsession


def relpath(filename):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)


def getband(freq):
    if freq.isnumeric():
        frequency = int(float(freq))
        if frequency >= 1800000 and frequency <= 2000000:
            return "160"
        if frequency >= 3500000 and frequency <= 4000000:
            return "80"
        if frequency >= 5332000 and frequency <= 5405000:
            return "60"
        if frequency >= 7000000 and frequency <= 7300000:
            return "40"
        if frequency >= 10100000 and frequency <= 10150000:
            return "30"
        if frequency >= 14000000 and frequency <= 14350000:
            return "20"
        if frequency >= 18068000 and frequency <= 18168000:
            return "17"
        if frequency >= 21000000 and frequency <= 21450000:
            return "15"
        if frequency >= 24890000 and frequency <= 24990000:
            return "12"
        if frequency >= 28000000 and frequency <= 29700000:
            return "10"
        if frequency >= 50000000 and frequency <= 54000000:
            return "6"
        if frequency >= 144000000 and frequency <= 148000000:
            return "2"
        if frequency >= 222000000 and frequency <= 225000000:
            return "222"
        if frequency >= 420000000 and frequency <= 450000000:
            return "432"
    else:
        return "OOB"


def getmode(rigmode):
    if rigmode == "CW" or rigmode == "CWR":
        return "CW"
    if rigmode == "USB" or rigmode == "LSB" or rigmode == "FM" or rigmode == "AM":
        return "PH"
    return "DI"  # All else digital


def sendRadio(cmd, arg):
    global band, mode, freq, power, rigonline
    rigCmd = bytes(cmd + " " + arg + "\n", "utf-8")
    if rigonline:
        if cmd == "B" and mode == "CW":
            if arg in dfreqCW:
                arg = "F " + str(dfreqCW[arg].replace(".", "")) + "000\n"
                rigCmd = bytes(arg, "utf-8")
                try:
                    rigctrlsocket.send(rigCmd)
                    rigCode = rigctrlsocket.recv(1024).decode().strip()
                except:
                    rigonline == False
            else:
                setStatusMsg("Unknown band specified")
        elif cmd == "B":
            if arg in dfreqPH:
                arg = "F " + str(dfreqPH[arg].replace(".", "")) + "000\n"
                rigCmd = bytes(arg, "utf-8")
                try:
                    rigctrlsocket.send(rigCmd)
                    rigCode = rigctrlsocket.recv(1024).decode().strip()
                except:
                    rigonline == False
        if cmd == "F":
            if arg.isnumeric() and int(arg) >= 1800000 and int(arg) <= 450000000:
                try:
                    rigctrlsocket.send(rigCmd)
                    rigCode = rigctrlsocket.recv(1024).decode().strip()
                except:
                    rigonline == False
            else:
                setStatusMsg("Specify frequency in Hz")
        elif cmd == "M":
            rigCmd = bytes(cmd + " " + arg + " 0\n", "utf-8")
            try:
                rigctrlsocket.send(rigCmd)
                rigCode = rigctrlsocket.recv(1024).decode().strip()
            except:
                rigonline == False
        elif cmd == "P":
            if arg.isnumeric() and int(arg) >= 1 and int(arg) <= 100:
                rigCmd = bytes("L RFPOWER " + str(float(arg) / 100) + "\n", "utf-8")
                try:
                    rigctrlsocket.send(rigCmd)
                    rigCode = rigctrlsocket.recv(1024).decode().strip()
                except:
                    rigonline == False
            else:
                setStatusMsg("Must be 1 <= Power <= 100")
    return


def pollRadio():
    global oldfreq, oldmode, oldpwr, rigctrlsocket, rigonline
    if rigonline:
        try:
            rigctrlsocket.settimeout(3.0)
            rigctrlsocket.send(b"f\n")
            newfreq = rigctrlsocket.recv(1024).decode().strip()
            rigctrlsocket.send(b"m\n")
            newmode = rigctrlsocket.recv(1024).decode().strip().split()[0]
            rigctrlsocket.send(b"l RFPOWER\n")
            newpwr = int(float(rigctrlsocket.recv(1024).decode().strip()) * 100)
            if newfreq != oldfreq or newmode != oldmode or newpwr != oldpwr:
                oldfreq = newfreq
                oldmode = newmode
                oldpwr = newpwr
                setband(str(getband(newfreq)))
                setmode(str(getmode(newmode)))
                setpower(str(newpwr))
                setfreq(str(newfreq))
        except Exception as e:
            rigonline = False


def checkRadio():
    global rigctrlsocket, rigctrlhost, rigctrlport, rigonline
    rigonline = True
    try:
        rigctrlsocket = socket.socket()
        rigctrlsocket.settimeout(0.1)
        rigctrlsocket.connect((rigctrlhost, int(rigctrlport)))
    except ConnectionRefusedError:
        logging.debug("checkRadio: ConnectionRefusedError")
        rigonline = False
    except BaseException as err:
        logging.debug(f"checkRadio: {err}")
        rigonline = False


def create_DB():
    """create a database and table if it does not exist"""
    global conn
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            sql_table = """ CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, callsign text NOT NULL, class text NOT NULL, section text NOT NULL, date_time text NOT NULL, band text NOT NULL, mode text NOT NULL, power INTEGER NOT NULL); """
            c.execute(sql_table)
            sql_table = """ CREATE TABLE IF NOT EXISTS preferences (id INTEGER, mycallsign TEXT DEFAULT 'YOURCALL', myclass TEXT DEFAULT 'YOURCLASS', mysection TEXT DEFAULT 'YOURSECTION', power TEXT DEFAULT '0', rigctrlhost TEXT default 'localhost', rigctrlport INTEGER DEFAULT 4532, altpower INTEGER DEFAULT 0, outdoors INTEGER DEFAULT 0, notathome INTEGER DEFAULT 0, satellite INTEGER DEFAULT 0); """
            c.execute(sql_table)
            conn.commit()
    except Error as e:
        logging.debug(f"create_DB: {e}")


def readpreferences():
    global mycall, myclass, mysection, power, rigctrlhost, rigctrlport, altpower, outdoors, notathome, satellite
    try:
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("select * from preferences where id = 1")
            pref = c.fetchall()
            if len(pref) > 0:
                for x in pref:
                    (
                        _,
                        mycall,
                        myclass,
                        mysection,
                        power,
                        rigctrlhost,
                        rigctrlport,
                        altpower,
                        outdoors,
                        notathome,
                        satellite,
                    ) = x
                    altpower = bool(altpower)
                    outdoors = bool(outdoors)
                    notathome = bool(notathome)
                    satellite = bool(satellite)
            else:
                sql = f"INSERT INTO preferences(id, mycallsign, myclass, mysection, power, rigctrlhost, rigctrlport, altpower, outdoors, notathome, satellite) VALUES(1,'{mycall}','{myclass}','{mysection}','{power}','{rigctrlhost}',{int(rigctrlport)},{int(altpower)},{int(outdoors)},{int(notathome)},{int(satellite)})"
                c.execute(sql)
                conn.commit()
    except Error as e:
        logging.debug(f"readPreferences: {e}")


def writepreferences():
    try:
        with sqlite3.connect(database) as conn:
            sql = f"UPDATE preferences SET mycallsign = '{mycall}', myclass = '{myclass}', mysection = '{mysection}', power = '{power}', rigctrlhost = '{rigctrlhost}', rigctrlport = {int(rigctrlport)}, altpower = {int(altpower)}, outdoors = {int(outdoors)}, notathome = {int(notathome)} WHERE id = 1"
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
    except Error as e:
        logging.debug(f"writepreferences: {e}")


def log_contact(logme):
    try:
        with sqlite3.connect(database) as conn:
            sql = "INSERT INTO contacts(callsign, class, section, date_time, band, mode, power) VALUES(?,?,?,datetime('now'),?,?,?)"
            cur = conn.cursor()
            cur.execute(sql, logme)
            conn.commit()
    except Error as e:
        logging.debug(f"log_contact: {e}")
        displayinfo(e)
    workedSections()
    sections()
    stats()
    logwindow()
    postcloudlog()


def delete_contact(contact):
    if contact:
        try:
            with sqlite3.connect(database) as conn:
                sql = f"delete from contacts where id={int(contact)}"
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
        except Error as e:
            logging.debug(f"delete_contact: {e}")
            displayinfo(e)
        workedSections()
        sections()
        stats()
        logwindow()
    else:
        setStatusMsg("Must specify a contact number")


def change_contact(qso):
    try:
        with sqlite3.connect(database) as conn:
            sql = f"update contacts set callsign = '{qso[1]}', class = '{qso[2]}', section = '{qso[3]}', date_time = '{qso[4]}', band = '{qso[5]}', mode = '{qso[6]}', power = '{qso[7]}'  where id='{qso[0]}'"
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
    except Error as e:
        logging.debug(f"change_contact: {e}")
        displayinfo(e)


def readSections():
    try:
        with open(relpath("arrl_sect.dat"), "r") as fd:  # read section data
            while 1:
                ln = fd.readline().strip()  # read a line and put in db
                if not ln:
                    break
                if ln[0] == "#":
                    continue
                try:
                    sec, st, canum, abbrev, name = str.split(ln, None, 4)
                    secName[abbrev] = abbrev + " " + name + " " + canum
                    secState[abbrev] = st
                    for i in range(len(abbrev) - 1):
                        p = abbrev[: -i - 1]
                        secPartial[p] = 1
                except ValueError as e:
                    logging.debug(f"readSections: Value error {e}")
    except IOError as e:
        logging.debug(f"readSections: IO Error {e}")


def sectionCheck(sec):
    if sec == "":
        sec = "^"
    seccheckwindow = curses.newpad(20, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    x = list(secName.keys())
    xx = list(filter(lambda y: y.startswith(sec), x))
    count = 0
    for xxx in xx:
        seccheckwindow.addstr(count, 1, secName[xxx])
        count += 1
    stdscr.refresh()
    seccheckwindow.refresh(0, 0, 12, 1, 20, 33)


readSections()


def readSCP():
    global scp
    with open(relpath("MASTER.SCP")) as f:
        scp = f.readlines()
    scp = list(map(lambda x: x.strip(), scp))


readSCP()


def superCheck(acall):
    return list(filter(lambda x: x.startswith(acall), scp))


def contacts():
    global stdscr
    rectangle(stdscr, 0, 0, 7, 55)
    contactslabel = "Recent Contacts"
    contactslabeloffset = (49 / 2) - len(contactslabel) / 2
    stdscr.addstr(0, int(contactslabeloffset), contactslabel)


def stats():
    global bandmodemult
    y, x = stdscr.getyx()
    with sqlite3.connect(database) as conn:
        c = conn.cursor()
        c.execute("select count(*) from contacts where mode = 'CW'")
        cwcontacts = str(c.fetchone()[0])
        c.execute("select count(*) from contacts where mode = 'PH'")
        phonecontacts = str(c.fetchone()[0])
        c.execute("select count(*) from contacts where mode = 'DI'")
        digitalcontacts = str(c.fetchone()[0])
        c.execute("select distinct band, mode from contacts")
        bandmodemult = len(c.fetchall())
        c.execute(
            "SELECT count(*) FROM contacts where datetime(date_time) >=datetime('now', '-15 Minutes')"
        )
        last15 = str(c.fetchone()[0])
        c.execute(
            "SELECT count(*) FROM contacts where datetime(date_time) >=datetime('now', '-1 Hours')"
        )
        lasthour = str(c.fetchone()[0])
    rectangle(stdscr, 0, 57, 7, 79)
    statslabel = "Score Stats"
    statslabeloffset = (25 / 2) - len(statslabel) / 2
    stdscr.addstr(0, 57 + int(statslabeloffset), statslabel)
    stdscr.addstr(1, 58, "Total CW:")
    stdscr.addstr(2, 58, "Total PHONE:")
    stdscr.addstr(3, 58, "Total DIGITAL:")
    stdscr.addstr(4, 58, "QSO POINTS:          ")
    stdscr.addstr(5, 58, "QSOs LAST HOUR:")
    stdscr.addstr(6, 58, "QSOs LAST 15MIN:")
    stdscr.addstr(1, 75, cwcontacts.rjust(4))
    stdscr.addstr(2, 75, phonecontacts.rjust(4))
    stdscr.addstr(3, 75, digitalcontacts.rjust(4))
    stdscr.addstr(4, 70, str(score()).rjust(9))
    stdscr.addstr(5, 76, lasthour.rjust(3))
    stdscr.addstr(6, 76, last15.rjust(3))
    stdscr.move(y, x)


def score():
    global bandmodemult
    qrpcheck()
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select count(*) as cw from contacts where mode = 'CW'")
    cw = str(c.fetchone()[0])
    c.execute("select count(*) as ph from contacts where mode = 'PH'")
    ph = str(c.fetchone()[0])
    c.execute("select count(*) as di from contacts where mode = 'DI'")
    di = str(c.fetchone()[0])
    c.execute("select distinct band, mode from contacts")
    bandmodemult = len(c.fetchall())
    conn.close()
    score = (int(cw) * 2) + int(ph) + (int(di) * 2)
    if qrp:
        score = score * 4
    elif not (highpower):
        score = score * 2
    score = score * bandmodemult
    score = (
        score
        + (500 * altpower)
        + (500 * outdoors)
        + (500 * notathome)
        + (500 * satellite)
    )
    return score


def qrpcheck():
    global qrp, highpower
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select count(*) as qrpc from contacts where mode = 'CW' and power > 5")
    log = c.fetchall()
    qrpc = list(log[0])[0]
    c.execute("select count(*) as qrpp from contacts where mode = 'PH' and power > 10")
    log = c.fetchall()
    qrpp = list(log[0])[0]
    c.execute("select count(*) as qrpd from contacts where mode = 'DI' and power > 10")
    log = c.fetchall()
    qrpd = list(log[0])[0]
    c.execute("select count(*) as highpower from contacts where power > 100")
    log = c.fetchall()
    highpower = bool(list(log[0])[0])
    conn.close()
    qrp = not (qrpc + qrpp + qrpd)


def getBandModeTally(band, mode):
    conn = ""
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        f"select count(*) as tally, MAX(power) as mpow from contacts where band = '{band}' AND mode ='{mode}'"
    )
    return c.fetchone()


def getbands():
    bandlist = []
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select DISTINCT band from contacts")
    x = c.fetchall()
    if x:
        for count in x:
            bandlist.append(count[0])
        return bandlist
    return []


def generateBandModeTally():
    blist = getbands()
    bmtfn = "Statistics.txt"
    with open(bmtfn, "w") as f:
        print("\t\tCW\tPWR\tDI\tPWR\tPH\tPWR", end="\r\n", file=f)
        print("-" * 60, end="\r\n", file=f)
        for b in bands:
            if b in blist:
                cwt = getBandModeTally(b, "CW")
                dit = getBandModeTally(b, "DI")
                pht = getBandModeTally(b, "PH")
                print(
                    f"Band:\t{b}\t{cwt[0]}\t{cwt[1]}\t{dit[0]}\t{dit[1]}\t{pht[0]}\t{pht[1]}",
                    end="\r\n",
                    file=f,
                )
                print("-" * 60, end="\r\n", file=f)


def getState(section):
    try:
        state = secState[section]
        if state != "--":
            return state
    except:
        return False
    return False


def adif():
    logname = "WFD.adi"
    with sqlite3.connect(database) as conn:
        c = conn.cursor()
        c.execute("select * from contacts order by date_time ASC")
        log = c.fetchall()
    counter = 0
    grid = False
    with open(logname, "w") as f:
        print("<ADIF_VER:5>2.2.0", end="\r\n", file=f)
        print("<EOH>", end="\r\n", file=f)
        for x in log:
            _, hiscall, hisclass, hissection, datetime, band, mode, _ = x
            if mode == "DI":
                mode = "RTTY"
            if mode == "PH":
                mode = "SSB"
            if mode == "CW":
                rst = "599"
            else:
                rst = "59"
            loggeddate = datetime[:10]
            loggedtime = datetime[11:13] + datetime[14:16]
            yy, xx = stdscr.getyx()
            stdscr.move(15, 1)
            stdscr.addstr(f"QRZ Gridsquare Lookup: {counter}")
            stdscr.move(yy, xx)
            stdscr.refresh()
            grid = False
            name = False
            try:
                if qrzsession:
                    payload = {"s": qrzsession, "callsign": hiscall}
                    r = requests.get(qrzurl, params=payload, timeout=3.0)
                    if r.status_code == 200:
                        xmlData = BeautifulSoup(r.text, "xml")
                        if xmlData.QRZDatabase.Callsign.grid:
                            grid = xmlData.QRZDatabase.Callsign.grid.string
                        name = (
                            xmlData.QRZDatabase.Callsign.fname.string
                            + " "
                            + xmlData.QRZDatabase.Callsign.name.string
                        )
            except:
                pass
            print(
                "<QSO_DATE:%s:d>%s"
                % (len("".join(loggeddate.split("-"))), "".join(loggeddate.split("-"))),
                end="\r\n",
                file=f,
            )
            print("<TIME_ON:%s>%s" % (len(loggedtime), loggedtime), end="\r\n", file=f)
            print(
                "<CALL:%s>%s" % (len(hiscall), hiscall),
                end="\r\n",
                file=open(logname, "a"),
            )
            print(
                "<MODE:%s>%s" % (len(mode), mode), end="\r\n", file=open(logname, "a")
            )
            print("<BAND:%s>%s" % (len(band + "M"), band + "M"), end="\r\n", file=f)
            try:
                print(
                    "<FREQ:%s>%s" % (len(dfreqPH[band]), dfreqPH[band]),
                    end="\r\n",
                    file=f,
                )
            except:
                pass
            print("<RST_SENT:%s>%s" % (len(rst), rst), end="\r\n", file=f)
            print("<RST_RCVD:%s>%s" % (len(rst), rst), end="\r\n", file=f)
            print(
                "<STX_STRING:%s>%s"
                % (len(myclass + " " + mysection), myclass + " " + mysection),
                end="\r\n",
                file=f,
            )
            print(
                "<SRX_STRING:%s>%s"
                % (len(hisclass + " " + hissection), hisclass + " " + hissection),
                end="\r\n",
                file=f,
            )
            print(
                "<ARRL_SECT:%s>%s" % (len(hissection), hissection), end="\r\n", file=f
            )
            print("<CLASS:%s>%s" % (len(hisclass), hisclass), end="\r\n", file=f)
            state = getState(hissection)
            if state:
                print("<STATE:%s>%s" % (len(state), state), end="\r\n", file=f)
            if grid:
                print("<GRIDSQUARE:%s>%s" % (len(grid), grid), end="\r\n", file=f)
            if name:
                print("<NAME:%s>%s" % (len(name), name), end="\r\n", file=f)
            print("<COMMENT:19>WINTER-FIELD-DAY", end="\r\n", file=f)
            print("<EOR>", end="\r\n", file=f)
            print("", end="\r\n", file=f)
    yy, xx = stdscr.getyx()
    stdscr.move(15, 1)
    stdscr.addstr("Done.                     ")
    stdscr.move(yy, xx)
    stdscr.refresh()


def parsecallsign(callsign):
    try:
        callelements = callsign.split("/")
    except:
        return callsign
    if len(callelements) == 3:
        return callelements[1]
    elif len(callelements) == 2:
        regex = re.compile("^([0-9])?[A-Za-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}$")
        if re.match(regex, callelements[0]):
            return callelements[0]
        else:
            return callelements[1]
    else:
        return callsign


def postcloudlog():
    global confData, hamdbOn, hamqthSession, qrzsession
    if not cloudlogapi:
        return
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select * from contacts order by id DESC")
    q = c.fetchone()
    conn.close()
    logid, hiscall, hisclass, hissection, datetime, band, mode, power = q
    grid = False
    name = False
    strippedcall = parsecallsign(hiscall)
    if hamqthSession:
        payload = {
            "id": hamqthSession,
            "callsign": strippedcall,
            "prg": confData["hamqth"]["appname"],
        }
        r = requests.get(confData["hamqth"]["url"], params=payload)
        if r.status_code == 200:
            xmlData = BeautifulSoup(r.text, "xml")
            try:
                grid = xmlData.HamQTH.search.grid.string
            except:
                hamqthSession = reinithamqth()
                r = requests.get(confData["hamqth"]["url"], params=payload)
                xmlData = BeautifulSoup(r.text, "xml")
                try:
                    grid = xmlData.HamQTH.search.grid.string
                except:
                    grid = ""
        try:
            name = xmlData.HamQTH.search.adr_name.string
        except:
            name = ""
        if len(grid) < 4 or len(grid) > 6:
            grid = ""
    if hamdbOn:
        grid = ""
        payload = strippedcall + "/xml/" + confData["hamdb"]["appname"]
        r = requests.get(confData["hamdb"]["url"] + "/" + payload)
        if r.status_code == 200:
            xmlData = BeautifulSoup(r.text, "xml")
            try:
                grid = xmlData.hamdb.callsign.grid.string
            except:
                grid = ""
        try:
            name = "%s %s" % (
                xmlData.hamdb.callsign.fname.string,
                xmlData.find("name").string,
            )
        except:
            name = ""
        if len(grid) < 4 or len(grid) > 6:
            grid = ""
    if qrzsession:
        payload = {"s": qrzsession, "callsign": strippedcall}
        r = requests.get(qrzurl, params=payload, timeout=1.0)
        if r.status_code == 200:
            xmlData = BeautifulSoup(r.text, "xml")
            try:
                grid = xmlData.QRZDatabase.Callsign.grid.string
            except:
                qrzsession = reinitqrz()
                r = requests.get(qrzurl, params=payload, timeout=1.0)
                xmlData = BeautifulSoup(r.text, "xml")
                try:
                    grid = xmlData.QRZDatabase.Callsign.grid.string
                except:
                    grid = ""
        try:
            name = "%s %s" % (
                xmlData.QRZDatabase.Callsign.fname.string,
                xmlData.find("name").string,
            )
        except:
            name = ""
        if len(grid) < 4 or len(grid) > 6:
            grid = ""
    if mode == "CW":
        rst = "599"
    else:
        rst = "59"
    loggeddate = datetime[:10]
    loggedtime = datetime[11:13] + datetime[14:16]
    adifq = "<QSO_DATE:%s:d>%s" % (
        len("".join(loggeddate.split("-"))),
        "".join(loggeddate.split("-")),
    )
    adifq += "<TIME_ON:%s>%s" % (len(loggedtime), loggedtime)
    adifq += "<CALL:%s>%s" % (len(hiscall), hiscall)
    adifq += "<MODE:%s>%s" % (len(mode), mode)
    adifq += "<BAND:%s>%s" % (len(band + "M"), band + "M")
    adifq += "<FREQ:%s>%s" % (len(dfreqPH[band]), dfreqPH[band])
    adifq += "<RST_SENT:%s>%s" % (len(rst), rst)
    adifq += "<RST_RCVD:%s>%s" % (len(rst), rst)
    adifq += "<STX_STRING:%s>%s" % (
        len(myclass + " " + mysection),
        myclass + " " + mysection,
    )
    adifq += "<SRX_STRING:%s>%s" % (
        len(hisclass + " " + hissection),
        hisclass + " " + hissection,
    )
    adifq += "<ARRL_SECT:%s>%s" % (len(hissection), hissection)
    adifq += "<CLASS:%s>%s" % (len(hisclass), hisclass)
    state = getState(hissection)
    if state:
        adifq += "<STATE:%s>%s" % (len(state), state)
    if grid:
        adifq += "<GRIDSQUARE:%s>%s" % (len(grid), grid)
    if name:
        adifq += "<NAME:%s>%s" % (len(name), name)
    adifq += "<COMMENT:14>ARRL-FIELD-DAY"
    adifq += "<EOR>"

    try:
        if int(confData["cloudlog"]["station_id"]) > 0:
            payload = {
                "key": cloudlogapi,
                "type": "adif",
                "station_profile_id": confData["cloudlog"]["station_id"],
                "string": adifq,
            }
    except:
        payload = {"key": cloudlogapi, "type": "adif", "string": adifq}

    jsonData = json.dumps(payload)
    logging.debug(f"{jsonData}")
    qsoUrl = cloudlogurl + "/qso"
    response = requests.post(qsoUrl, jsonData)


def cabrillo():

    bonuses = 0

    catpower = ""
    if qrp:
        catpower = "QRP"
    elif highpower:
        catpower = "HIGH"
    else:
        catpower = "LOW"
    with open("WFDLOG.txt", "w", encoding="ascii") as f:
        print("START-OF-LOG: 3.0", end="\r\n", file=f)
        print("CREATED-BY: K6GTE Winter Field Day Logger", end="\r\n", file=f)
        print("CONTEST: WFD", end="\r\n", file=f)
        print("CALLSIGN:", mycall, end="\r\n", file=f)
        print("LOCATION:", end="\r\n", file=f)
        print("ARRL-SECTION:", mysection, end="\r\n", file=f)
        print("CATEGORY:", myclass, end="\r\n", file=f)
        print("CATEGORY-POWER: " + catpower, end="\r\n", file=f)
        if altpower:
            print(
                "SOAPBOX: 500 points for not using commercial power", end="\r\n", file=f
            )
            bonuses = bonuses + 500
        if outdoors:
            print("SOAPBOX: 500 points for setting up outdoors", end="\r\n", file=f)
            bonuses = bonuses + 500
        if notathome:
            print(
                "SOAPBOX: 500 points for setting up away from home", end="\r\n", file=f
            )
            bonuses = bonuses + 500
        if satellite:
            print("SOAPBOX: 500 points for working satellite", end="\r\n", file=f)
            bonuses = bonuses + 500
        print(f"SOAPBOX: BONUS Total {bonuses}", end="\r\n", file=f)

        print(f"CLAIMED-SCORE: {score()}", end="\r\n", file=f)
        print(f"OPERATORS:{mycall}", end="\r\n", file=f)
        print("NAME: ", end="\r\n", file=f)
        print("ADDRESS: ", end="\r\n", file=f)
        print("ADDRESS-CITY: ", end="\r\n", file=f)
        print("ADDRESS-STATE: ", end="\r\n", file=f)
        print("ADDRESS-POSTALCODE: ", end="\r\n", file=f)
        print("ADDRESS-COUNTRY: ", end="\r\n", file=f)
        print("EMAIL: ", end="\r\n", file=f)
        with sqlite3.connect(database) as conn:
            c = conn.cursor()
            c.execute("select * from contacts order by date_time ASC")
            log = c.fetchall()
            for x in log:
                _, hiscall, hisclass, hissection, datetime, band, mode, _ = x
                loggeddate = datetime[:10]
                loggedtime = datetime[11:13] + datetime[14:16]
                print(
                    f"QSO: {band}M {mode} {loggeddate} {loggedtime} {mycall} {myclass} {mysection} {hiscall} {hisclass} {hissection}",
                    end="\r\n",
                    file=f,
                )
        print("END-OF-LOG:", end="\r\n", file=f)

    generateBandModeTally()

    oy, ox = stdscr.getyx()
    window = curses.newpad(10, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    window.addstr(0, 0, "Log written to: WFDLOG.txt")
    window.addstr(1, 0, "Stats written to: Statistics.txt")
    window.addstr(2, 0, "ADIF written to: WFD.adi")
    stdscr.refresh()
    window.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)
    adif()
    writepreferences()
    statusline()
    stats()


def logwindow():
    global contacts, contactsOffset, logNumber
    contactsOffset = 0  # clears scroll position
    callfiller = "          "
    classfiller = "   "
    sectfiller = "   "
    bandfiller = "   "
    modefiller = "  "
    zerofiller = "000"
    contacts = curses.newpad(1000, 80)
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select * from contacts order by date_time desc")
    log = c.fetchall()
    conn.close()
    logNumber = 0
    for x in log:
        logid, hiscall, hisclass, hissection, datetime, band, mode, power = x
        logid = zerofiller[: -len(str(logid))] + str(logid)
        hiscall = hiscall + callfiller[: -len(hiscall)]
        hisclass = hisclass + classfiller[: -len(hisclass)]
        hissection = hissection + sectfiller[: -len(hissection)]
        band = band + sectfiller[: -len(band)]
        mode = mode + modefiller[: -len(mode)]
        logline = f"{logid} {hiscall} {hisclass} {hissection} {datetime} {band} {mode} {power}"
        contacts.addstr(logNumber, 0, logline)
        logNumber += 1
    stdscr.refresh()
    contacts.refresh(0, 0, 1, 1, 6, 54)


def logup():
    global contacts, contactsOffset, logNumber
    contactsOffset += 1
    if contactsOffset > (logNumber - 6):
        contactsOffset = logNumber - 6
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logpagedown():
    global contacts, contactsOffset, logNumber
    contactsOffset += 10
    if contactsOffset > (logNumber - 6):
        contactsOffset = logNumber - 6
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logpageup():
    global contacts, contactsOffset
    contactsOffset -= 10
    if contactsOffset < 0:
        contactsOffset = 0
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def logdown():
    global contacts, contactsOffset
    contactsOffset -= 1
    if contactsOffset < 0:
        contactsOffset = 0
    contacts.refresh(contactsOffset, 0, 1, 1, 6, 54)


def dupCheck(acall):
    global hisclass, hissection
    oy, ox = stdscr.getyx()
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)

    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute(
        f"select callsign, class, section, band, mode from contacts where callsign like '{acall}' order by band"
    )
    log = c.fetchall()
    conn.close()
    counter = 0
    for x in log:
        decorate = ""
        hiscall, hisclass, hissection, hisband, hismode = x
        if hisband == band and hismode == mode:
            decorate = curses.color_pair(1)
            curses.flash()
            curses.beep()
        else:
            decorate = curses.A_NORMAL
        scpwindow.addstr(counter, 0, f"{hiscall}: {hisband} {hismode}", decorate)
        counter = counter + 1
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def displaySCP(matches):
    scpwindow = curses.newpad(1000, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    for x in matches:
        wy, wx = scpwindow.getyx()
        if (33 - wx) < len(str(x)):
            scpwindow.move(wy + 1, 0)
        scpwindow.addstr(str(x) + " ")
    stdscr.refresh()
    scpwindow.refresh(0, 0, 12, 1, 20, 33)


def workedSections():
    global wrkdsections
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select distinct section from contacts")
    all_rows = c.fetchall()
    wrkdsections = str(all_rows)
    wrkdsections = (
        wrkdsections.replace("('", "")
        .replace("',), ", ",")
        .replace("',)]", "")
        .replace("[", "")
        .split(",")
    )


def workedSection(section):
    if section in wrkdsections:
        # return curses.A_BOLD
        return curses.color_pair(1)
    else:
        return curses.A_DIM


def sectionsCol1():
    rectangle(stdscr, 8, 35, 19, 43)
    stdscr.addstr(8, 36, "   DX  ", curses.A_REVERSE)
    stdscr.addstr(9, 36, "   DX  ", workedSection("DX"))
    stdscr.addstr(10, 36, "   1   ", curses.A_REVERSE)
    stdscr.addstr(11, 36, "CT", workedSection("CT"))
    stdscr.addstr(11, 41, "RI", workedSection("RI"))
    stdscr.addstr(12, 36, "EMA", workedSection("EMA"))
    stdscr.addstr(12, 41, "VT", workedSection("VT"))
    stdscr.addstr(13, 36, "ME", workedSection("ME"))
    stdscr.addstr(13, 40, "WMA", workedSection("WMA"))
    stdscr.addstr(14, 36, "NH", workedSection("NH"))
    stdscr.addstr(15, 36, "   2   ", curses.A_REVERSE)
    stdscr.addstr(16, 36, "ENY", workedSection("ENY"))
    stdscr.addstr(16, 40, "NNY", workedSection("NNY"))
    stdscr.addstr(17, 36, "NLI", workedSection("NLI"))
    stdscr.addstr(17, 40, "SNJ", workedSection("SNJ"))
    stdscr.addstr(18, 36, "NNJ", workedSection("NNJ"))
    stdscr.addstr(18, 40, "WNY", workedSection("WNY"))


def sectionsCol2():
    rectangle(stdscr, 8, 44, 19, 52)
    stdscr.addstr(8, 45, "   3   ", curses.A_REVERSE)
    stdscr.addstr(9, 45, "DE", workedSection("DE"))
    stdscr.addstr(9, 49, "MDC", workedSection("MDC"))
    stdscr.addstr(10, 45, "EPA", workedSection("EPA"))
    stdscr.addstr(10, 49, "WPA", workedSection("WPA"))
    stdscr.addstr(11, 45, "   4   ", curses.A_REVERSE)
    stdscr.addstr(12, 45, "AL", workedSection("AL"))
    stdscr.addstr(12, 50, "SC", workedSection("SC"))
    stdscr.addstr(13, 45, "GA", workedSection("GA"))
    stdscr.addstr(13, 49, "SFL", workedSection("SFL"))
    stdscr.addstr(14, 45, "KY", workedSection("KY"))
    stdscr.addstr(14, 50, "TN", workedSection("TN"))
    stdscr.addstr(15, 45, "NC", workedSection("NC"))
    stdscr.addstr(15, 50, "VA", workedSection("VA"))
    stdscr.addstr(16, 45, "NFL", workedSection("NFL"))
    stdscr.addstr(16, 50, "VI", workedSection("VI"))
    stdscr.addstr(17, 45, "PR", workedSection("PR"))
    stdscr.addstr(17, 49, "WCF", workedSection("WCF"))


def sectionsCol3():
    rectangle(stdscr, 8, 53, 21, 61)
    stdscr.addstr(8, 54, "   5   ", curses.A_REVERSE)
    stdscr.addstr(9, 54, "AR", workedSection("AR"))
    stdscr.addstr(9, 58, "NTX", workedSection("NTX"))
    stdscr.addstr(10, 54, "LA", workedSection("LA"))
    stdscr.addstr(10, 59, "OK", workedSection("OK"))
    stdscr.addstr(11, 54, "MS", workedSection("MS"))
    stdscr.addstr(11, 58, "STX", workedSection("STX"))
    stdscr.addstr(12, 54, "NM", workedSection("NM"))
    stdscr.addstr(12, 58, "WTX", workedSection("WTX"))
    stdscr.addstr(13, 54, "   6   ", curses.A_REVERSE)
    stdscr.addstr(14, 54, "EB", workedSection("EB"))
    stdscr.addstr(14, 58, "SCV", workedSection("SCV"))
    stdscr.addstr(15, 54, "LAX", workedSection("LAX"))
    stdscr.addstr(15, 58, "SDG", workedSection("SDG"))
    stdscr.addstr(16, 54, "ORG", workedSection("ORG"))
    stdscr.addstr(16, 59, "SF", workedSection("SF"))
    stdscr.addstr(17, 54, "PAC", workedSection("PAC"))
    stdscr.addstr(17, 58, "SJV", workedSection("SJV"))
    stdscr.addstr(18, 54, "SB", workedSection("SB"))
    stdscr.addstr(18, 59, "SV", workedSection("SV"))


def sectionsCol4():
    rectangle(stdscr, 8, 62, 21, 70)
    stdscr.addstr(8, 63, "   7   ", curses.A_REVERSE)
    stdscr.addstr(9, 63, "AK", workedSection("AK"))
    stdscr.addstr(9, 68, "NV", workedSection("NV"))
    stdscr.addstr(10, 63, "AZ", workedSection("AZ"))
    stdscr.addstr(10, 68, "OR", workedSection("OR"))
    stdscr.addstr(11, 63, "EWA", workedSection("EWA"))
    stdscr.addstr(11, 68, "UT", workedSection("UT"))
    stdscr.addstr(12, 63, "ID", workedSection("ID"))
    stdscr.addstr(12, 67, "WWA", workedSection("WWA"))
    stdscr.addstr(13, 63, "MT", workedSection("MT"))
    stdscr.addstr(13, 68, "WY", workedSection("WY"))
    stdscr.addstr(14, 63, "   8   ", curses.A_REVERSE)
    stdscr.addstr(15, 63, "MI", workedSection("MI"))
    stdscr.addstr(15, 68, "WV", workedSection("WV"))
    stdscr.addstr(16, 63, "OH", workedSection("OH"))
    stdscr.addstr(17, 63, "   9   ", curses.A_REVERSE)
    stdscr.addstr(18, 63, "IL", workedSection("IL"))
    stdscr.addstr(18, 68, "WI", workedSection("WI"))
    stdscr.addstr(19, 63, "IN", workedSection("IN"))


def sectionsCol5():
    rectangle(stdscr, 8, 71, 21, 79)
    stdscr.addstr(8, 72, "   0   ", curses.A_REVERSE)
    stdscr.addstr(9, 72, "CO", workedSection("CO"))
    stdscr.addstr(9, 77, "MO", workedSection("MO"))
    stdscr.addstr(10, 72, "IA", workedSection("IA"))
    stdscr.addstr(10, 77, "ND", workedSection("ND"))
    stdscr.addstr(11, 72, "KS", workedSection("KS"))
    stdscr.addstr(11, 77, "NE", workedSection("NE"))
    stdscr.addstr(12, 72, "MN", workedSection("MN"))
    stdscr.addstr(12, 77, "SD", workedSection("SD"))
    stdscr.addstr(13, 72, "CANADA ", curses.A_REVERSE)
    stdscr.addstr(14, 72, "AB", workedSection("AB"))
    stdscr.addstr(14, 77, "NT", workedSection("NT"))
    stdscr.addstr(15, 72, "BC", workedSection("BC"))
    stdscr.addstr(15, 76, "ONE", workedSection("ONE"))
    stdscr.addstr(16, 72, "GTA", workedSection("GTA"))
    stdscr.addstr(16, 76, "ONN", workedSection("ONN"))
    stdscr.addstr(17, 72, "MAR", workedSection("MAR"))
    stdscr.addstr(17, 76, "ONS", workedSection("ONS"))
    stdscr.addstr(18, 72, "MB", workedSection("MB"))
    stdscr.addstr(18, 77, "QC", workedSection("QC"))
    stdscr.addstr(19, 72, "NL", workedSection("NL"))
    stdscr.addstr(19, 77, "SK", workedSection("SK"))
    stdscr.addstr(20, 72, "PE", workedSection("PE"))


def sections():
    workedSections()
    sectionsCol1()
    sectionsCol2()
    sectionsCol3()
    sectionsCol4()
    sectionsCol5()
    stdscr.refresh()


def entry():
    rectangle(stdscr, 8, 0, 10, 18)
    stdscr.addstr(8, 1, "CALL")
    rectangle(stdscr, 8, 19, 10, 25)
    stdscr.addstr(8, 20, "Class")
    rectangle(stdscr, 8, 26, 10, 34)
    stdscr.addstr(8, 27, "Section")


def clearentry():
    global inputFieldFocus, hiscall, hissection, hisclass, kbuf
    hiscall = ""
    hissection = ""
    hisclass = ""
    kbuf = ""
    inputFieldFocus = 0
    displayInputField(2)
    displayInputField(1)
    displayInputField(0)


def YorN(boolean):
    if boolean:
        return "Y"
    else:
        return "N"


def highlightBonus(bonus):
    if bonus:
        return curses.color_pair(1)
    else:
        return curses.A_DIM


def setStatusMsg(msg):
    oy, ox = stdscr.getyx()
    window = curses.newpad(10, 33)
    rectangle(stdscr, 11, 0, 21, 34)
    window.addstr(0, 0, msg)
    stdscr.refresh()
    window.refresh(0, 0, 12, 1, 20, 33)
    stdscr.move(oy, ox)


def statusline():
    y, x = stdscr.getyx()
    now = datetime.datetime.now().isoformat(" ")[5:19].replace("-", "/")
    utcnow = datetime.datetime.utcnow().isoformat(" ")[5:19].replace("-", "/")

    try:
        stdscr.addstr(22, 62, "LOC " + now)
        stdscr.addstr(23, 62, "UTC " + utcnow)
    except curses.error as e:
        pass

    strfreq = freq.rjust(9)
    strfreq = f"{strfreq[0:3]}.{strfreq[3:6]}.{strfreq[6:9]}"

    strband = band
    if band == None or band == "None":
        strband = "OOB"

    if strband == "222":
        strband = "1.25"
    elif strband == "432":
        strband = "70"

    suffix = ""

    if strband == "OOB":
        suffix = ""
    elif int(freq) > 225000000:
        suffix = "cm"
    else:
        suffix = "m"

    strband += suffix

    if len(strband) < 4:
        strband += " "

    stdscr.addstr(20, 35, " HamDB   HamQTH   ")
    stdscr.addstr(20, 42, YorN(hamdbOn), highlightBonus(hamdbOn))
    stdscr.addstr(20, 51, YorN(hamqthSession), highlightBonus(hamqthSession))
    stdscr.addstr(21, 35, " QRZ   Cloudlog   ")
    stdscr.addstr(21, 40, YorN(qrzsession), highlightBonus(qrzsession))
    stdscr.addstr(21, 51, YorN(cloudLogOn), highlightBonus(cloudLogOn))
    stdscr.addstr(23, 0, "Band       Freq             Mode   ")
    stdscr.addstr(23, 5, strband.rjust(5), curses.A_REVERSE)
    stdscr.addstr(23, 16, strfreq, curses.A_REVERSE)
    stdscr.addstr(23, 33, mode, curses.A_REVERSE)
    stdscr.addstr(22, 37, "                         ")
    stdscr.addstr(
        22,
        37,
        " " + mycall + "|" + myclass + "|" + mysection + "|" + power + "w ",
        curses.A_REVERSE,
    )
    stdscr.addstr(22, 0, "Bonus")
    stdscr.addstr(22, 6, "AltPwr", highlightBonus(altpower))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Outdoor", highlightBonus(outdoors))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("NotHome", highlightBonus(notathome))
    stdscr.addch(curses.ACS_VLINE)
    stdscr.addstr("Sat", highlightBonus(satellite))
    stdscr.addstr(23, 37, "Rig                     ")
    stdscr.addstr(
        23, 41, rigctrlhost.lower() + ":" + str(rigctrlport), highlightBonus(rigonline)
    )

    stdscr.move(y, x)


def setpower(p):
    global power
    try:
        int(p)
    except:
        p = "0"
    if p is None or p == "":
        p = "0"
    if int(p) > 0 and int(p) < 101:
        power = p
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be 1 <= Power <= 100")


def setband(b):
    global band
    band = b
    statusline()


def setmode(m):
    global mode
    mode = m
    statusline()


def setfreq(f):
    global freq
    freq = f
    statusline()


def setcallsign(c):
    global mycall
    regex = re.compile("^([0-9])?[A-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}$")
    if re.match(regex, str(c)):
        mycall = str(c)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid call sign")


def setclass(c):
    global myclass
    regex = re.compile("^[0-9]{1,2}[HhIiOo]$")
    if re.match(regex, str(c)):
        myclass = str(c)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid station class")


def setsection(s):
    global mysection, sections
    if s and str(s) in validSections:
        mysection = str(s)
        writepreferences()
        statusline()
    else:
        setStatusMsg("Must be valid section")


def setrigctrlhost(o):
    global rigctrlhost
    rigctrlhost = str(o)
    writepreferences()
    statusline()


def setrigctrlport(r):
    global rigctrlport
    rigctrlport = str(r)
    writepreferences()
    rigctrlport = int(r)
    statusline()


def claimAltPower():
    global altpower
    if altpower:
        altpower = False
    else:
        altpower = True
    setStatusMsg("Alt Power set to: " + str(altpower))
    writepreferences()
    statusline()
    stats()


def claimOutdoors():
    global outdoors
    if outdoors:
        outdoors = False
    else:
        outdoors = True
    setStatusMsg("Outdoor bonus set to: " + str(outdoors))
    writepreferences()
    statusline()
    stats()


def claimNotHome():
    global notathome
    if notathome:
        notathome = False
    else:
        notathome = True
    setStatusMsg("Away bonus set to: " + str(notathome))
    writepreferences()
    statusline()
    stats()


def claimSatellite():
    global satellite
    if satellite:
        satellite = False
    else:
        satellite = True
    setStatusMsg("Satellite bonus set to: " + str(satellite))
    writepreferences()
    statusline()
    stats()


def displayHelp(page):
    rectangle(stdscr, 11, 0, 21, 34)
    wy, wx = stdscr.getyx()
    if page == 1:
        help = [
            "Main Help Screen                 ",
            "                                 ",
            ".H this message  |.1 Outdoors    ",
            ".0 rigctrl help  |.2 AltPwr      ",
            ".Q quit program  |.3 AwayFromHome",
            ".Kyourcall       |.4 Satellite   ",
            ".Cyourclass      |.E### edit QSO ",
            ".Syoursection    |.D### del QSO  ",
            "[ESC] Abort Input|.L Generate Log",
        ]
    elif page == 2:
        help = [
            "Rig Control Help Screen          ",
            "                                 ",
            ".0 this message  |               ",
            ".H main help     |               ",
            ".Irighost        |.Rrigport      ",
            ".Ffreq (in Hz)   |.Ppower (in W) ",
            ".Mmode (eg USB)  |.Bband (eg 20) ",
            "                                 ",
            "                                 ",
        ]
    else:
        help = [
            "Help Screen                      ",
            ".H Main Help Screen              ",
            ".0 Rig Control Help Screen       ",
        ]
    stdscr.move(12, 1)
    count = 0
    for x in help:
        stdscr.addstr(12 + count, 1, x)
        count = count + 1
    stdscr.move(wy, wx)
    stdscr.refresh()


def displayinfo(info):
    y, x = stdscr.getyx()
    stdscr.move(20, 1)
    stdscr.addstr(info)
    stdscr.move(y, x)
    stdscr.refresh()


def displayLine():
    filler = "                        "
    line = kbuf + filler[: -len(kbuf)]
    stdscr.move(9, 1)
    stdscr.addstr(line)
    stdscr.move(9, len(kbuf) + 1)
    stdscr.refresh()


def displayInputField(field):
    filler = "                 "
    if field == 0:
        filler = "                 "
        y = 1
    elif field == 1:
        filler = "     "
        y = 20
    elif field == 2:
        filler = "       "
        y = 27
    stdscr.move(9, y)
    if kbuf == "":
        stdscr.addstr(filler)
    else:
        line = kbuf + filler[: -len(kbuf)]
        stdscr.addstr(line.upper())
    stdscr.move(9, len(kbuf) + y)
    stdscr.refresh()


def processcommand(cmd):
    global band, mode, power, quit, rigonline
    cmd = cmd[1:].upper()
    if cmd == "Q":  # Quit
        quit = True
        return
    if cmd[:1] == "F":  # Set Radio Frequency
        sendRadio(cmd[:1], cmd[1:])
        return
    if cmd[:1] == "B":  # Change Band
        if cmd[1:] and cmd[1:] in bands:
            if rigonline:
                sendRadio(cmd[:1], cmd[1:])
                return
            else:
                setband(cmd[1:])
        else:
            setStatusMsg("Specify valid band")
        return
    if cmd[:1] == "M":  # Change Mode
        if rigonline == False:
            if cmd[1:] == "CW" or cmd[1:] == "PH" or cmd[1:] == "DI":
                setmode(cmd[1:])
            else:
                setStatusMsg("Must be CW, DI, PH")
        else:
            if (
                cmd[1:] == "USB"
                or cmd[1:] == "LSB"
                or cmd[1:] == "CW"
                or cmd[1:] == "RTTY"
                or cmd[1:] == "AM"
                or cmd[1:] == "FM"
            ):
                sendRadio(cmd[:1], cmd[1:])
            else:
                setStatusMsg("Must be AM, FM, CW, *SB, RTTY")
        return
    if cmd[:1] == "P":  # Change Power
        if rigonline:
            sendRadio(cmd[:1], cmd[1:])
        else:
            setpower(cmd[1:])
        return
    if cmd[:1] == "D":  # Delete Contact
        delete_contact(cmd[1:])
        return
    if cmd[:1] == "E":  # Edit QSO
        editQSO(cmd[1:])
        return
    if cmd[:1] == "H":  # Print Help
        displayHelp(1)
        return
    if cmd[:1] == "0":  # Print Rig Control Help
        displayHelp(2)
        return
    if cmd[:1] == "K":  # Set your Call Sign
        setcallsign(cmd[1:])
        return
    if cmd[:1] == "C":  # Set your class
        setclass(cmd[1:])
        return
    if cmd[:1] == "S":  # Set your section
        setsection(cmd[1:])
        return
    if cmd[:1] == "I":  # Set rigctld host
        regex1 = re.compile("localhost")
        regex2 = re.compile("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*")
        if re.match(regex1, cmd[1:].lower()) or re.match(regex2, cmd[1:].lower()):
            setrigctrlhost(cmd[1:])
            rigonline = False
        else:
            setStatusMsg("Must be IP or localhost")
        return
    if cmd[:1] == "R":  # Set rigctld port
        regex = re.compile("[0-9]{1,5}")
        if (
            re.match(regex, cmd[1:].lower())
            and int(cmd[1:]) > 1023
            and int(cmd[1:]) < 65536
        ):
            setrigctrlport(cmd[1:])
            rigonline = False
        else:
            setStatusMsg("Must be 1024 <= Port <= 65535")
        return
    if cmd[:1] == "L":  # Generate Cabrillo Log
        cabrillo()
        return
    if cmd[:1] == "1":  # Claim Alt Power Bonus
        claimAltPower()
        return
    if cmd[:1] == "2":  # Claim Outdoor Bonus
        claimOutdoors()
        return
    if cmd[:1] == "3":  # Claim Not Home Bonus
        claimNotHome()
        return
    if cmd[:1] == "4":  # Claim Satellite Bonus
        claimSatellite()
        return
    curses.flash()
    curses.beep()


def proc_key(key):
    global inputFieldFocus, hiscall, hissection, hisclass, kbuf
    if key == 9 or key == Space:
        inputFieldFocus += 1
        if inputFieldFocus > 2:
            inputFieldFocus = 0
        if inputFieldFocus == 0:
            hissection = kbuf  # store any input to previous field
            stdscr.move(9, 1)  # move focus to call field
            kbuf = hiscall  # load current call into buffer
            stdscr.addstr(kbuf)
        if inputFieldFocus == 1:
            hiscall = kbuf  # store any input to previous field
            dupCheck(hiscall)
            stdscr.move(9, 20)  # move focus to class field
            kbuf = hisclass  # load current class into buffer
            stdscr.addstr(kbuf)
        if inputFieldFocus == 2:
            hisclass = kbuf  # store any input to previous field
            stdscr.move(9, 27)  # move focus to section field
            kbuf = hissection  # load current section into buffer
            stdscr.addstr(kbuf)
        return
    elif key == BackSpace:
        if kbuf != "":
            kbuf = kbuf[0:-1]
            if inputFieldFocus == 0 and len(kbuf) < 3:
                displaySCP(superCheck("^"))
            if inputFieldFocus == 0 and len(kbuf) > 2:
                displaySCP(superCheck(kbuf))
            if inputFieldFocus == 2:
                sectionCheck(kbuf)
        displayInputField(inputFieldFocus)
        return
    elif key == EnterKey:
        if inputFieldFocus == 0:
            hiscall = kbuf
        elif inputFieldFocus == 1:
            hisclass = kbuf
        elif inputFieldFocus == 2:
            hissection = kbuf
        if hiscall[:1] == ".":  # process command
            processcommand(hiscall)
            clearentry()
            return
        if hiscall == "" or hisclass == "" or hissection == "":
            return
        isCall = re.compile(
            "^(([0-9])?[A-z]{1,2}[0-9]/)?[A-Za-z]{1,2}[0-9]{1,3}[A-Za-z]{1,4}(/[A-Za-z0-9]{1,3})?$"
        )
        if re.match(isCall, hiscall):
            contact = (hiscall, hisclass, hissection, band, mode, int(power))
            log_contact(contact)
            clearentry()
        else:
            setStatusMsg("Must be valid call sign")
        return
    elif key == Escape:
        clearentry()
        return
    elif key == Space:
        return
    elif key == 258:  # key down
        logup()
        pass
    elif key == 259:  # key up
        logdown()
        pass
    elif key == 338:  # page down
        logpagedown()
        pass
    elif key == 339:  # page up
        logpageup()
        pass
    elif curses.ascii.isascii(key):
        if len(kbuf) < maxFieldLength[inputFieldFocus]:
            kbuf = kbuf.upper() + chr(key).upper()
            if inputFieldFocus == 0 and len(kbuf) > 2:
                displaySCP(superCheck(kbuf))
            if inputFieldFocus == 2 and len(kbuf) > 0:
                sectionCheck(kbuf)
    displayInputField(inputFieldFocus)


def edit_key(key):
    global editFieldFocus, qso, quit
    if key == 9:
        editFieldFocus += 1
        if editFieldFocus > 7:
            editFieldFocus = 1
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    elif key == BackSpace:
        if qso[editFieldFocus] != "":
            qso[editFieldFocus] = qso[editFieldFocus][0:-1]
        displayEditField(editFieldFocus)
        return
    elif key == EnterKey:
        change_contact(qso)
        qsoew.erase()
        stdscr.clear()
        rectangle(stdscr, 0, 0, 7, 55)
        contactslabel = "Recent Contacts"
        contactslabeloffset = (49 / 2) - len(contactslabel) / 2
        stdscr.addstr(0, int(contactslabeloffset), contactslabel)
        logwindow()
        sections()
        stats()
        displayHelp(1)
        entry()
        stdscr.move(9, 1)
        quit = True
        return
    elif key == Escape:
        qsoew.erase()
        stdscr.clear()
        rectangle(stdscr, 0, 0, 7, 55)
        contactslabel = "Recent Contacts"
        contactslabeloffset = (49 / 2) - len(contactslabel) / 2
        stdscr.addstr(0, int(contactslabeloffset), contactslabel)
        logwindow()
        sections()
        stats()
        displayHelp(1)
        entry()
        stdscr.move(9, 1)
        quit = True
        return
    elif key == Space:
        return
    elif key == 258:  # arrow down
        editFieldFocus += 1
        if editFieldFocus > 7:
            editFieldFocus = 1
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    elif key == 259:  # arrow up
        editFieldFocus -= 1
        if editFieldFocus < 1:
            editFieldFocus = 7
        qsoew.move(editFieldFocus, 10)  # move focus to call field
        qsoew.addstr(qso[editFieldFocus])
        return
    elif curses.ascii.isascii(key):
        # displayinfo("eff:"+str(editFieldFocus)+" mefl:"+str(maxEditFieldLength[editFieldFocus]))
        if len(qso[editFieldFocus]) < maxEditFieldLength[editFieldFocus]:
            qso[editFieldFocus] = qso[editFieldFocus].upper() + chr(key).upper()
    displayEditField(editFieldFocus)


def displayEditField(field):
    global qso
    filler = "                 "
    if field == 1:
        filler = "                 "
    elif field == 2:
        filler = "     "
    elif field == 3:
        filler = "       "
    qsoew.move(field, 10)
    if qso[field] == "":
        qsoew.addstr(filler)
    else:
        line = qso[field] + filler[: -len(qso[field])]
        qsoew.addstr(line.upper())
    qsoew.move(field, len(qso[field]) + 10)
    qsoew.refresh()


def EditClickedQSO(line):
    global qsoew, qso, quit
    record = (
        contacts.instr((line - 1) + contactsOffset, 0, 55)
        .decode("utf-8")
        .strip()
        .split()
    )
    if record == []:
        return
    qso = [
        record[0],
        record[1],
        record[2],
        record[3],
        record[4] + " " + record[5],
        record[6],
        record[7],
        record[8],
    ]
    qsoew = curses.newwin(10, 40, 6, 10)
    qsoew.keypad(True)
    qsoew.nodelay(True)
    qsoew.box()
    qsoew.addstr(1, 1, "Call   : " + qso[1])
    qsoew.addstr(2, 1, "Class  : " + qso[2])
    qsoew.addstr(3, 1, "Section: " + qso[3])
    qsoew.addstr(4, 1, "At     : " + qso[4])
    qsoew.addstr(5, 1, "Band   : " + qso[5])
    qsoew.addstr(6, 1, "Mode   : " + qso[6])
    qsoew.addstr(7, 1, "Powers : " + qso[7])
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")
    displayEditField(1)
    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.1)
        if quit:
            quit = False
            break


def editQSO(q):
    if q == False or q == "":
        setStatusMsg("Must specify a contact number")
        return
    global qsoew, qso, quit
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("select * from contacts where id=" + q)
    log = c.fetchall()
    conn.close()
    if not log:
        return
    qso = ["", "", "", "", "", "", "", ""]
    qso[0], qso[1], qso[2], qso[3], qso[4], qso[5], qso[6], qso[7] = log[0]
    qsoew = curses.newwin(10, 40, 6, 10)
    qsoew.keypad(True)
    qsoew.nodelay(True)
    qsoew.box()
    qsoew.addstr(1, 1, "Call   : " + qso[1])
    qsoew.addstr(2, 1, "Class  : " + qso[2])
    qsoew.addstr(3, 1, "Section: " + qso[3])
    qsoew.addstr(4, 1, "At     : " + qso[4])
    qsoew.addstr(5, 1, "Band   : " + qso[5])
    qsoew.addstr(6, 1, "Mode   : " + qso[6])
    qsoew.addstr(7, 1, "Powers : " + str(qso[7]))
    qsoew.addstr(8, 1, "[Enter] to save          [Esc] to exit")
    displayEditField(1)
    while 1:
        statusline()
        stdscr.refresh()
        qsoew.refresh()
        c = qsoew.getch()
        if c != -1:
            edit_key(c)
        else:
            time.sleep(0.1)
        if quit:
            quit = False
            break


def main(s):
    global pollTime, stdscr, conn, rigonline
    conn = create_DB()
    curses.start_color()
    curses.use_default_colors()
    if curses.can_change_color():
        curses.init_color(curses.COLOR_MAGENTA, 1000, 640, 0)
        curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
        curses.init_color(curses.COLOR_CYAN, 500, 500, 500)
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    stdscr.attrset(curses.color_pair(0))
    stdscr.clear()
    contacts()
    sections()
    entry()
    logwindow()
    readpreferences()
    stats()
    displayHelp(1)
    stdscr.refresh()
    stdscr.move(9, 1)
    while 1:
        statusline()
        stdscr.refresh()
        ch = stdscr.getch()
        if ch == curses.KEY_MOUSE:
            buttons = ""
            try:
                _, x, y, _, buttons = curses.getmouse()
                if buttons == 65536:
                    logdown()
                if buttons == 2097152:
                    logup()
                if buttons == 8 and 0 < y < 7 and 0 < x < 56:
                    EditClickedQSO(y)
            except curses.error:
                pass
            pass
        elif ch != -1:
            proc_key(ch)
        else:
            time.sleep(0.1)
        if quit:
            break
        if datetime.datetime.now() > pollTime:
            if rigonline == False:
                checkRadio()
            else:
                pollRadio()
                pollTime = datetime.datetime.now()+datetime.timedelta(seconds=5)


if __name__ == "__main__":
    wrapper(main)
