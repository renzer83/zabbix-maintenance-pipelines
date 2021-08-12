from pyzabbix import ZabbixAPI
import configparser
import json
from datetime import datetime
import time

config = configparser.ConfigParser()
config.read('config.ini')
USER = config.get('zabbix', 'user')
PASSWORD = config.get('zabbix', 'password')
SERVER = config.get('zabbix', 'server')
HOSTGROUPNAME= config.get('zabbix', 'hostgroupname')
MAINTENANCENAME= config.get('zabbix', 'maintenancename')
TIMERDEPLOY= int(config.get('zabbix', 'timerdeploy'))

def date_to_seconds(timestamp):
    return time.mktime(timestamp.timetuple())

def time_to_seconds(timestamp):
    return timestamp.hour * 60 + timestamp.minute

def connect(server, user, password):
    zapi = ZabbixAPI(server)
    zapi.session.verify = False
    zapi.login(user, password)
    return zapi

def validmaintenance(name, apiconnector, groupids, period):
    timeperiods = {
        'timeperiod_type': 0,
        'day': 1,
        'month': 0,
        'dayofweek': 0,
        'every': 1,
        'start_date': date_to_seconds(datetime.now()),
        'start_time': time_to_seconds(datetime.now()),
        'period': period,
    }
    try:
        filternameobj={}
        response = apiconnector.maintenance.get(selectTimeperiods="extend")
        for listmaintenance in response:
            if name in listmaintenance["name"]:
                filternameobj = listmaintenance
        print(json.dumps(filternameobj,indent=4))
        del filternameobj["name"]
        del filternameobj["maintenance_type"]
        filternameobj["description"]="Manutenção para deploys aplicacionais: {}".format(datetime.now())    
        filternameobj["active_since"]=int(time.time())
        filternameobj["active_till"]=int(time.time())+period
        filternameobj["groupids"] = [groupids]
        filternameobj["timeperiods"].append(timeperiods)
        return filternameobj
    except KeyError as error:
        return False

def updatenewperiodmaintenance(apiconnector, body):
    apiconnector.maintenance.update(body)

def createmaintenance(apiconnector, name, groupid, period):
    maintenancearray = {
        "name":name,
        "description": "Manutenção para deploys aplicacionais: {}".format(datetime.now()),
        "active_since":int(time.time()),
        "active_till":int(time.time())+period,
        "groupids": [groupid],
        'timeperiods': [{
            'timeperiod_type': 0,
            'day': 1,
            'month': 0,
            'dayofweek': 0,
            'every': 1,
            'start_date': date_to_seconds(datetime.now()),
            'start_time': time_to_seconds(datetime.now()),
            'period': period,
    }]
    }
    print(json.dumps(maintenancearray, indent=4))
    apiconnector.maintenance.create(maintenancearray)
    

if __name__ == "__main__":
    api = connect(SERVER, USER, PASSWORD)
    groupid=""
    hostgroups = api.hostgroup.get()
    for listgroups in hostgroups:
        if HOSTGROUPNAME in listgroups["name"]:
            groupid = listgroups["groupid"]
    responsefunct = validmaintenance(MAINTENANCENAME,api, groupid, TIMERDEPLOY)                
    if responsefunct is not False:
        print(json.dumps(responsefunct,indent=4))
        updatenewperiodmaintenance(api, responsefunct)
    elif responsefunct is False:
        createmaintenance(api, MAINTENANCENAME, groupid, TIMERDEPLOY)
