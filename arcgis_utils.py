import datetime


def arcgis_new_feature_no_location(tags, fields, message_time):
    new_feature = {
        "attributes": {
            "location_timestamp": message_time,
        }
    }

    # Add all tags
    new_feature["attributes"].update(tags)
    # Add all fields
    new_feature["attributes"].update(fields)

    return new_feature


def arcgis_new_feature_with_location(tags, fields, message_time):
    new_feature = {
        "attributes": {
            "location_timestamp": message_time,
        }
    }

    if "latitude" in fields and "longitude" in fields:
        new_feature["geometry"] = {
            "x": fields["longitude"],
            "y": fields["latitude"],
            "spatialReference": {"wkid": 4326, "latestWkid": 4326}
        }

    # Add all tags
    new_feature["attributes"].update(tags)
    # Add all fields
    new_feature["attributes"].update(fields)

    return new_feature


def arcgis_update_feature_no_location(feature, tags, fields, message_time):
    feature.attributes["location_timestamp"] = message_time

    # Add all tags
    feature.attributes.update(tags)
    # Add all fields
    feature.attributes.update(fields)

    return feature


def arcgis_update_feature_with_location(feature, tags, fields, message_time):
    feature.attributes["location_timestamp"] = message_time

    if "latitude" in fields and "longitude" in fields:
        if not (fields['latitude'] == 0 and fields['longitude'] == 0):
            feature.geometry = {
                "x": fields["longitude"],
                "y": fields["latitude"],
                "spatialReference": {"wkid": 4326, "latestWkid": 4326}
            }

    # Add all tags
    feature.attributes.update(tags)
    # Add all fields
    feature.attributes.update(fields)

    return feature