gcloud functions deploy pubsub-to-arcgis \
--project=tts-to-arcgis \
--gen2 \
--runtime=python310 \
--region=europe-west1 \
--source=. \
--entry-point=subscribe \
--trigger-topic=from-tts