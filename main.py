# gcloud functions deploy tts-to-arc --project=tts-to-arcgis --gen2 --runtime=python310 --region=europe-west1 --source=. --entry-point=uplink_message --trigger-http --allow-unauthenticated
import datetime

import dateutil.parser
import functions_framework
import requests
from arcgis.gis import GIS
from flask import make_response

from arcgis_utils import arcgis_new_feature_with_location, arcgis_new_feature_no_location

client_id = "EMNjWCgcdZQQ2QDz"
client_secret = "08f22cb1a8dc45579bac24f9ca39d6fa"
item_id = "db6efcf98c244866b73e82f810c131f9"


def flatten_json(y):
    out = {}

    # https://www.geeksforgeeks.org/flattening-json-objects-in-python/
    def flatten(x, name=''):

        # If the Nested key-value
        # pair is of dict type
        if type(x) is dict:

            for a in x:
                flatten(x[a], name + a + '_')

        # If the Nested key-value
        # pair is of list type
        elif type(x) is list:

            i = 0

            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out


@functions_framework.http
def uplink_message(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    Note:
        For more information on how Flask integrates with Cloud
        Functions, see the `Writing HTTP functions` page.
        <https://cloud.google.com/functions/docs/writing/http#http_frameworks>
    """
    print(datetime.datetime.now())

    tts_domain = request.headers.get('X-Tts-Domain')
    if tts_domain is None:
        return make_response("TTS domain header not present", 400)
    tts_api_key = request.headers.get('X-Downlink-Apikey')
    if tts_api_key is None:
        return make_response("Api Key header not present", 400)

    print(tts_domain, tts_api_key)

    try:
        post_data = request.get_json()
    except:
        return make_response("Can't parse uplink json", 500)

    if post_data is None:
        return make_response("POST data empty", 400)

    device_id = post_data['end_device_ids']['device_id']
    device_eui = post_data['end_device_ids']['dev_eui']
    application_id = post_data['end_device_ids']['application_ids']['application_id']
    print(application_id, device_id, device_eui)

    uplink_time = post_data['received_at']
    uplink_datetime = dateutil.parser.parse(uplink_time)
    print("Uplink time", uplink_datetime)

    # Get the device attributes and name
    url = 'https://'+tts_domain+'/api/v3/applications/'+application_id+'/devices/'+device_id+'?field_mask=name,attributes,locations'
    device_response = requests.get(url, headers={"Authorization": "Bearer "+tts_api_key})
    try:
        device_json = device_response.json()
    except:
        return make_response("device json error", 500)
    if device_json is None:
        return make_response("device json empty", 500)

    print(device_json)

    if 'message' in device_json:
        return make_response(device_json['message'], 500)

    try:
        name = device_json['name']
    except:
        name = device_id
    try:
        attributes = device_json['attributes']
    except:
        return make_response("device json does not contain attributes", 500)

    print(name)
    print(attributes)

    try:
        client_id = attributes['arcgis-client-id']
    except:
        return make_response("Attributes does not contain arcgis_client_id", 400)
    try:
        client_secret = attributes['arcgis-client-secret']
    except:
        return make_response("Attributes does not contain arcgis_client_secret", 400)
    try:
        item_id = attributes['arcgis-item-id']
    except:
        return make_response("Attributes does not contain arcgis_item_id", 400)

    decoded_payload = post_data['uplink_message']['decoded_payload']
    flat_payload = flatten_json(decoded_payload)
    print(decoded_payload)
    print(flat_payload)

    # Use location from console if no location is present in payload
    if 'locations' in device_json:
        if 'user' in device_json['locations']:
            console_latitude = device_json['locations']['user']['latitude']
            console_longitude = device_json['locations']['user']['longitude']
            console_altitude = device_json['locations']['user']['altitude']

            if console_latitude != 0 and console_longitude != 0:
                if not ('latitude' in flat_payload and 'longitude' in flat_payload):
                    flat_payload['latitude'] = console_latitude
                    flat_payload['longitude'] = console_longitude
                    flat_payload['altitude'] = console_altitude

    # If payloads contains a time, use that rather than uplink_datetime
    message_time = uplink_datetime
    if 'timestamp' in flat_payload:
        message_time = datetime.datetime.fromtimestamp(flat_payload['timestamp'])

    # Add device name to payload
    if 'name' not in flat_payload:
        flat_payload['name'] = name

    # Get token
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': "client_credentials"
    }
    request = requests.get('https://www.arcgis.com/sharing/rest/oauth2/token',
                           params=params)
    response = request.json()
    token = ""
    try:
        token = response["access_token"]
    except:
        print(response)
        return

    gis = GIS(token=token, referer="https://backend.izinto.cloud", expiration=9999)

    izinto_item = gis.content.get(item_id)

    # Append feature to layer or table
    for feature_layer in izinto_item.layers:
        properties = feature_layer.properties
        if 'geometryType' in properties and feature_layer.properties['geometryType'] == 'esriGeometryPoint':
            print("Adding GeometryPoint")
            new_feature = arcgis_new_feature_with_location(flat_payload, message_time)
            print(new_feature)
            result = feature_layer.edit_features(adds=[new_feature])
            # print(result)

    for feature_layer in izinto_item.tables:
        properties = feature_layer.properties
        if 'type' in properties and feature_layer.properties['type'] == 'Table':
            print("Adding to Table")
            new_feature = arcgis_new_feature_no_location(flat_payload, message_time)
            print(new_feature)
            result = feature_layer.edit_features(adds=[new_feature])
            # print(result)

    # Update existing feature
    # for feature_layer in izinto_item.layers:
    #     properties = feature_layer.properties
    #     if 'geometryType' in properties and feature_layer.properties['geometryType'] == 'esriGeometryPoint':
    #         print("Updating GeometryPoint")
    #
    #         where_clause = f"name={name}"
    #         feature_response = feature_layer.query(where=where_clause)
    #
    #         if len(feature_response) == 0:
    #             print("Creating new feature")
    #             # Create a blank feature in case it does not exist yet
    #             new_feature = arcgis_new_feature_with_location(flat_payload, message_time)
    #             print(new_feature)
    #             result = feature_layer.edit_features(adds=[new_feature])
    #             print(result)
    #
    #         else:
    #             # Only update the first one. Rest should be manually deleted.
    #             feature = feature_response.features[0]
    #
    #             # Only update if the current message is newer than the last one written to arcgis
    #             if message_time.timestamp()*1000 <= feature.attributes['location_timestamp']:
    #                 break
    #
    #             feature = arcgis_update_feature_with_location(feature, flat_payload, message_time)
    #             print(feature)
    #
    #             result = feature_layer.edit_features(updates=[feature])
    #             print(result)
    #
    # for feature_layer in izinto_item.tables:
    #     properties = feature_layer.properties
    #     properties = feature_layer.properties
    #     if 'type' in properties and feature_layer.properties['type'] == 'Table':
    #         print("Updating Table")
    #
    #         where_clause = f"name={name}"
    #         feature_response = feature_layer.query(where=where_clause)
    #
    #         if len(feature_response) == 0:
    #             print("Creating new feature")
    #             # Create a blank feature in case it does not exist yet
    #             new_feature = arcgis_new_feature_no_location(flat_payload, message_time)
    #             print(new_feature)
    #             result = feature_layer.edit_features(adds=[new_feature])
    #             print(result)
    #
    #         else:
    #             # Only update the first one. Rest should be manually deleted.
    #             feature = feature_response.features[0]
    #
    #             # Only update if the current message is newer than the last one written to arcgis
    #             if message_time.timestamp()*1000 <= feature.attributes['location_timestamp']:
    #                 return
    #
    #             feature = arcgis_update_feature_no_location(feature, flat_payload, message_time)
    #             print(feature)
    #
    #             result = feature_layer.edit_features(updates=[feature])
    #             print(result)

    return make_response("done", 200)
