gcloud functions deploy tts-to-pubsub \
    --project=tts-to-arcgis \
    --gen2 \
    --runtime=python310 \
    --region=europe-west1 \
    --source=. \
    --entry-point=uplink_message \
    --trigger-http \
    --allow-unauthenticated