import requests
import json
import urllib3
import os
import pickle
import platform

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


global CONTENT_TYPE, req_args, BASE_URL_PREFIX, VSOM_HEADER_PREFIX, GET_CAMERA_URL, session
CONTENT_TYPE = 'application/json'
req_args = {"verify": False}
BASE_URL_PREFIX = 'https://%s/ismserver/json'
session = requests.session()
VSOM_HEADER_PREFIX = 'x-ism-sid='
GET_CAMERA_URL = '/camera/getCameras'

PLATFORM = platform.system()

if PLATFORM.lower() == 'WINDOWS'.lower():
    DIV = '\\'
else:
    DIV = '/'

VSOMS_PROPERTIES_FILE = DIV + 'vsoms.properties'
PICKLE_FILE = "cameras.pickle"



def get_camera_location(camera_name):
    location_list = get_vsoms(camera_name)

    return location_list


def get_vsoms(camera_name):
    # This is the dictionary which contains camera_name as key and location as value
    cameras_from_all_vsoms = {}
    cameras_from_all_vsoms.clear()
    locations_list = None
    # First load the dictionary from pickle file
    try:
        cameras_from_all_vsoms = pickle.load(open(PICKLE_FILE, "rb"))
    except FileNotFoundError as e:
        print(e)

    ''' Below if else conditions checks:
    1. if dictionary cameras_from_all_vsoms is not empty, get all the locations in a list and return. If it doesn't
       finds the camera, it calls all VSOMs
    2. if dictionary cameras_from_all_vsoms is empty then calls all VSOMs pulling their cameras creating the dictionary
     & return list of locations        
    '''
    if cameras_from_all_vsoms.__len__() > 0:
        locations_list = list(v for k, v in cameras_from_all_vsoms.items().__iter__() if camera_name.lower() in k.lower())
        if locations_list.__len__() == 0:
            locations_list = get_locations_of_camera(cameras_from_all_vsoms, camera_name)

    elif cameras_from_all_vsoms.__len__() == 0:
        locations_list = get_locations_of_camera(cameras_from_all_vsoms, camera_name)

    return locations_list


def get_locations_of_camera(cameras_from_all_vsoms, camera_name):
    cwd = os.getcwd()
    cwd = os.path.dirname(cwd)

    vsom_property_file_path = cwd + VSOMS_PROPERTIES_FILE
    all_vsoms = open(vsom_property_file_path, "r")
    if all_vsoms.__sizeof__() > 0:
        for line in all_vsoms:
            if not line.startswith('#'):
                cameras_from_all_vsoms.update(call_and_get_cameras(line))
            else:
                print("please uncomment %s in vsoms.properties file" % line)
    try:
        pickle.dump(cameras_from_all_vsoms, open(PICKLE_FILE, "wb"))
    except Exception as e:
        print("Some error while adding the cameras from %s to pickle file, error is %s" % (line, e))

    locations_list = list(v for k, v in cameras_from_all_vsoms.items().__iter__() if camera_name.lower() in k.lower())

    return locations_list


def call_and_get_cameras(line):
    array = line.split()
    vsom_ip = array[0]
    uid = array[1]
    pwd = array[2]
    #print("url is %s and uid is %s with pwd as %s" %(vsom_ip, uid, pwd))

    base_url = get_base_url(vsom_ip)
    vsom_session_id = get_vsom_Session(base_url, vsom_ip, uid, pwd)
    #print(vsom_session_id)
    if vsom_session_id is None:
        print("FAILED LOGGING TO %s, PLEASE CHECK ABOVE ERROR MESSAGE " %(vsom_ip))
    else:
        cameras = get_vsom_cameras(base_url, vsom_session_id)

    return cameras


def get_base_url(vsom_ip):
    return BASE_URL_PREFIX % vsom_ip


def get_vsom_Session(base_url, vsom_ip, uid, pwd):
    login_url = '/authentication/login'
    data = {'username': uid, 'password': pwd, 'domain': ''}
    vsomLoginheaders = {'content-type': CONTENT_TYPE, 'Accept': CONTENT_TYPE}

    url = base_url + login_url
    response = session.post(url, data=json.dumps(data), headers=vsomLoginheaders, **req_args)

    resp_json = response.json()

    if resp_json['status']['errorType'] == "FAILURE":
        vsom_session_id = None
        print("Failed for %s with error message: %s" %(vsom_ip, resp_json['status']['errorMsg']))
    else:
        vsom_session_id = resp_json['data']['uid']

    return vsom_session_id


def get_vsom_cameras(base_url, vsom_session_id):
    vsomAuthHeader = VSOM_HEADER_PREFIX + vsom_session_id
    vsomLoginheaders = {'content-type': CONTENT_TYPE, 'Cookie': vsomAuthHeader}

    url = base_url + GET_CAMERA_URL

    input = {"filter": {
        "includeEncoderVideoPortAssociationsOnly": False,
        "includeContactClosurePortAssociationsOnly": False,
        "byNotInRecommendedget_camFirmwareVersion": False,
        "byLocationUids": ["40000000-0000-0000-0000-000000000005"],
        "includeSubLocations": True,
        "byNameContains": "",
        "byObjectType": "device_vs_camera",
        "byTagsContains": "",
        "pageInfo": {
            "start": 0,
            "limit": 500
        }
    }}
    response = session.post(url, data=json.dumps(input), headers=vsomLoginheaders, **req_args)
    response_json = response.json()
    total_rows = response_json['data']['totalRows']
    print("Total no of cameras received from %s is %s" %(base_url, total_rows))
    cameras_dict = {}
    if total_rows > 0:
        for cam in response_json['data']['items']:
            # Please add here other elements which you want to add in the dictionary
            cameras_dict[cam['name']] = cam['locationRef']['refName']
    else:
        print("There are no cameras received from VSOM %s", base_url)

    return cameras_dict


print(get_camera_location("sdfsdfsdf"))



