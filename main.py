import base64
import json
import re
import traceback
from io import BytesIO
import os 

import functions_framework
import numpy as np
import requests
from PIL import Image
from cryptonets_python_sdk.settings.configuration import ConfigObject, PARAMETERS
from cryptonets_python_sdk.factor import FaceFactor
from cryptonets_python_sdk.settings.loggingLevel import LoggingLevel

class SessionStatus:
    AGE_UNKNOWN = "AGE_UNKNOWN"
    BELOW_THRESHOLD = "AGE_BELOW_THRESHOLD"
    ABOVE_THRESHOLD = "AGE_ABOVE_THRESHOLD"



@functions_framework.http
def estimate_age(request):
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
    try:
        AGE_THRESHOLD= request_json.get('AGE_THRESHOLD', 22)
        if request.get_json(silent=True):
            request_json = request.get_json(silent=True)
        elif request.data:
            request_json = json.loads(request.data)
        else:
            return (json.dumps({
                "status ": -1,
                "message ": "Invalid Payload"}), 500, headers)
    except Exception as e:
        print('Error:{} '.format(e))
        return (json.dumps({
            "status ": -1,
            "message ": "Something went wrong while parsing the payload"}), 500, headers)
    if not request_json.get('api_key', None):
        print("Invalid Payload: api_key not found")

        return (json.dumps({
            "status ": -1,
            "message ": "Invalid Payload: api_key not found"}), 500, headers)

    if not request_json.get('image_b64', None):
        print("Invalid Payload: image_b64 not found")
        return (json.dumps({
            "status ": -1,
            "message ": "Invalid Payload: image_b64 not found"}), 500, headers)

    print('api_key:{} \n \n image_b64 : {}!'.format(request_json['api_key'], request_json['image_b64']))

    try:
        image_data_b64 = re.sub('^data:image/.+;base64,', '', request_json.get('image_b64', None))
        image_data = np.array(Image.open(BytesIO(base64.b64decode(image_data_b64))).convert('RGB'))
    except Exception as e:
        print('Error:{} '.format(e))
        return (json.dumps({
            "status ": -1,
            "message ": "Invalid Image : Something went wrong while reading the image"}), 500, headers)
    try:
        server_url = "https://api.cryptonets.ai/node/"
        api_key = request_json.get('api_key', None)
        response = requests.request("POST", server_url + "api-key/checkApiKeyValid",
                                    headers={'Content-Type': 'application/json'},
                                    data=json.dumps({"api_key": api_key
                                                     }))
        if response.json().get('status', -1) != 0:
            return (json.dumps({"status ": -1,
                                "message ": "Invalid Apikey",
                                "faces": []}), 200, headers)
        
        # Mapping of API request keys to their corresponding PARAMETERS keys
        parameter_mapping = {
            "INPUT_IMAGE_FORMAT": PARAMETERS.INPUT_IMAGE_FORMAT,
            "CONTEXT_STRING": PARAMETERS.CONTEXT_STRING,
            "INPUT_TYPE": PARAMETERS.INPUT_TYPE,
            "BLUR_THRESHOLD_ENROLL_PRED": PARAMETERS.BLUR_THRESHOLD_ENROLL_PRED,
            "CONF_SCORE_THR_ENROLL": PARAMETERS.CONF_SCORE_THR_ENROLL,
            "THRESHOLD_PROFILE_ENROLL": PARAMETERS.THRESHOLD_PROFILE_ENROLL,
            "THRESHOLD_HIGH_VERTICAL_ENROLL": PARAMETERS.THRESHOLD_HIGH_VERTICAL_ENROLL,
            "THRESHOLD_DOWN_VERTICAL_ENROLL": PARAMETERS.THRESHOLD_DOWN_VERTICAL_ENROLL,
            "THRESHOLD_USER_RIGHT": PARAMETERS.THRESHOLD_USER_RIGHT,
            "THRESHOLD_USER_LEFT": PARAMETERS.THRESHOLD_USER_LEFT,
            "THRESHOLD_USER_TOO_FAR": PARAMETERS.THRESHOLD_USER_TOO_FAR,
            "THRESHOLD_USER_TOO_CLOSE": PARAMETERS.THRESHOLD_USER_TOO_CLOSE,
            "SPOOF_FILTER_THRESHOLD": PARAMETERS.SPOOF_FILTER_THRESHOLD,
            "ANGLE_ROTATION_LEFT_THRESHOLD": PARAMETERS.ANGLE_ROTATION_LEFT_THRESHOLD,
            "ANGLE_ROTATION_RIGHT_THRESHOLD": PARAMETERS.ANGLE_ROTATION_RIGHT_THRESHOLD,
            "SKIP_ANTISPOOF": PARAMETERS.SKIP_ANTISPOOF,
            "SINGLE_FACE_AGE_RESUL": PARAMETERS.SINGLE_FACE_AGE_RESUL,
            "FACE_TOO_BRIGHT": PARAMETERS.FACE_TOO_BRIGHT,
            "FACE_TOO_DARK": PARAMETERS.FACE_TOO_DARK
        }

        config_param = {}
        for api_key, param_key in parameter_mapping.items():
            if api_key in request_json:
                config_param[param_key] = request_json[api_key]


        face_factor = FaceFactor(logging_level=LoggingLevel.off)
        if request_json.get('relaxed_params', None):
            config = ConfigObject(config_param={

            PARAMETERS.INPUT_IMAGE_FORMAT: config_param.get("INPUT_IMAGE_FORMAT", "rgb"),
            PARAMETERS.CONTEXT_STRING: config_param.get("CONTEXT_STRING", "enroll"),
            PARAMETERS.INPUT_TYPE: config_param.get("INPUT_TYPE", "face"),
            PARAMETERS.BLUR_THRESHOLD_ENROLL_PRED: config_param.get("BLUR_THRESHOLD_ENROLL_PRED", 8),
            PARAMETERS.CONF_SCORE_THR_ENROLL: config_param.get("CONF_SCORE_THR_ENROLL", 0.5),
            PARAMETERS.THRESHOLD_PROFILE_ENROLL: config_param.get("THRESHOLD_PROFILE_ENROLL", 0.8),
            PARAMETERS.THRESHOLD_HIGH_VERTICAL_ENROLL: config_param.get("THRESHOLD_HIGH_VERTICAL_ENROLL", -0.3),
            PARAMETERS.THRESHOLD_DOWN_VERTICAL_ENROLL: config_param.get("THRESHOLD_DOWN_VERTICAL_ENROLL", 0.3),
            PARAMETERS.THRESHOLD_USER_RIGHT: config_param.get("THRESHOLD_USER_RIGHT", 0.01),
            PARAMETERS.THRESHOLD_USER_LEFT: config_param.get("THRESHOLD_USER_LEFT", 0.99),
            PARAMETERS.THRESHOLD_USER_TOO_FAR: config_param.get("THRESHOLD_USER_TOO_FAR", 0.1),
            PARAMETERS.THRESHOLD_USER_TOO_CLOSE: config_param.get("THRESHOLD_USER_TOO_CLOSE", 1),
            PARAMETERS.SPOOF_FILTER_THRESHOLD: config_param.get("SPOOF_FILTER_THRESHOLD", 0.699999988079071),
            PARAMETERS.ANGLE_ROTATION_LEFT_THRESHOLD: config_param.get("ANGLE_ROTATION_LEFT_THRESHOLD", 40.0),
            PARAMETERS.ANGLE_ROTATION_RIGHT_THRESHOLD: config_param.get("ANGLE_ROTATION_RIGHT_THRESHOLD", 40.0),
            PARAMETERS.SKIP_ANTISPOOF: config_param.get("SKIP_ANTISPOOF", True),
            PARAMETERS.SINGLE_FACE_AGE_RESUL: config_param.get("SINGLE_FACE_AGE_RESUL", False),
            PARAMETERS.FACE_TOO_BRIGHT: config_param.get("FACE_TOO_BRIGHT", 0.85),
            PARAMETERS.FACE_TOO_DARK: config_param.get("FACE_TOO_DARK", 0.1)

            })
            age_handle = face_factor.estimate_age(image_data=image_data,config=config)
        
        elif config_param:  
            config = ConfigObject(config_param=config_param)
            age_handle = face_factor.estimate_age(image_data=image_data, config=config)
        else:
            age_handle = face_factor.estimate_age(image_data=image_data)
            
        response = []

        for index, face in enumerate(age_handle.face_objects):
            if face.age is None or face.age == -1:
                    session_status=SessionStatus.AGE_UNKNOWN
            elif face.age < AGE_THRESHOLD:
                    session_status=SessionStatus.BELOW_THRESHOLD
            else:
                       session_status=SessionStatus.ABOVE_THRESHOLD

            face = {"return_code": face.return_code, "message": face.message, "age": face.age,
                    "BBox_top_left": face.bounding_box.top_left_coordinate.__str__(),
                    "BBox_bottom_right": face.bounding_box.bottom_right_coordinate.__str__(),
                    "session_status":session_status }
            response.append(face)

        if not len(response):
            return (json.dumps({"status ": -1,
                                "message ": "Invalid Apikey or no face found",
                                "faces": response}), 200, headers)
        else:
            return (json.dumps({"status ": 0,
                                "message ": "Ok",
                                "faces": response}), 200, headers)
    except Exception as e:
        print('Error:{} '.format(e))
        print(traceback.format_exc())
        return (json.dumps({
            "status ": -1,
            "message ": "Something went wrong"}), 500, headers)
