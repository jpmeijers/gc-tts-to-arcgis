from google.cloud import pubsub_v1
import functions_framework
import json


project_id = "tts-to-arcgis"
topic_id = "from-tts"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)


@functions_framework.http
def uplink_message(request):
    """
    HTTP Cloud Function.
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
    # print(datetime.datetime.now())

    tts_domain = request.headers.get('X-Tts-Domain')
    if tts_domain is None:
        return ("TTS domain header not present", 400)
    tts_api_key = request.headers.get('X-Downlink-Apikey')
    if tts_api_key is None:
        return ("Api Key header not present", 400)

    # print(tts_domain, tts_api_key)

    try:
        post_data = request.get_json()
    except:
        return ("Can't parse uplink json", 500)

    if post_data is None:
        return ("POST data empty", 400)

    data = {'tts_domain': tts_domain, 'tts_api_key': tts_api_key, 'data': post_data}

    future = publisher.publish(topic_path, json.dumps(data).encode("utf-8"))
    try:
        message_id = future.result()
    except:
        return ("Error publishing message", 500)

    return (f"Published messages with id {message_id}.", 200)