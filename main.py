# gcloud functions deploy tts-to-arc --project=tts-to-arcgis --gen2 --runtime=python310 --region=europe-west1 --source=. --entry-point=uplink_message --trigger-http --allow-unauthenticated
import datetime

import functions_framework
import requests
from arcgis.gis import GIS

from arcgis_utils import arcgis_new_feature_with_location, arcgis_new_feature_no_location

client_id = "EMNjWCgcdZQQ2QDz"
client_secret = "08f22cb1a8dc45579bac24f9ca39d6fa"
item_id = "db6efcf98c244866b73e82f810c131f9"


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
    tags = {"hardware_serial": "1234", "installation_id": 1, "logger_id": 1, "site_id": 1}
    fields = {"latitude": -34.0, "longitude": 19.0}

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

    for feature_layer in izinto_item.layers:
        properties = feature_layer.properties
        if 'geometryType' in properties and feature_layer.properties['geometryType'] == 'esriGeometryPoint':
            print("Adding GeometryPoint")
            new_feature = arcgis_new_feature_with_location(tags, fields, datetime.datetime.now())
            print(new_feature)
            result = feature_layer.edit_features(adds=[new_feature])
            print(result)

    for feature_layer in izinto_item.tables:
        properties = feature_layer.properties
        if 'type' in properties and feature_layer.properties['type'] == 'Table':
            print("Adding to Table")
            new_feature = arcgis_new_feature_no_location(tags, fields, datetime.datetime.now())
            print(new_feature)
            result = feature_layer.edit_features(adds=[new_feature])
            print(result)

    return 'Hello World!'


if __name__ == '__main__':
    uplink_message(None)