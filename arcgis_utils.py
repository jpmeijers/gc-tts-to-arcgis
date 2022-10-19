def arcgis_new_feature_no_location(payload, message_time):
    new_feature = {
        "attributes": {
            "location_timestamp": message_time,
        }
    }

    # Add all fields
    new_feature["attributes"].update(payload)

    return new_feature


def arcgis_new_feature_with_location(payload, message_time):
    new_feature = {
        "attributes": {
            "location_timestamp": message_time,
        }
    }

    if "latitude" in payload and "longitude" in payload:
        new_feature["geometry"] = {
            "x": payload["longitude"],
            "y": payload["latitude"],
            "spatialReference": {"wkid": 4326, "latestWkid": 4326}
        }

    # Add all fields
    new_feature["attributes"].update(payload)

    return new_feature


def arcgis_update_feature_no_location(feature, payload, message_time):
    feature.attributes["location_timestamp"] = message_time

    # Add all fields
    feature.attributes.update(payload)

    return feature


def arcgis_update_feature_with_location(feature, payload, message_time):
    feature.attributes["location_timestamp"] = message_time

    if "latitude" in payload and "longitude" in payload:
        if not (payload['latitude'] == 0 and payload['longitude'] == 0):
            feature.geometry = {
                "x": payload["longitude"],
                "y": payload["latitude"],
                "spatialReference": {"wkid": 4326, "latestWkid": 4326}
            }

    # Add all fields
    feature.attributes.update(payload)

    return feature