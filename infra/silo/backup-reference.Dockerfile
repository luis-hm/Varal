# Coolify metadata-only application for the native backup schedule.
# DO NOT DEPLOY. There is deliberately no executable in this image.
# Its storage record references the existing varal-silo-data Docker volume.
# Never delete the Coolify application with delete_volumes=true.
FROM scratch
CMD ["/backup-reference-only-no-runtime"]
