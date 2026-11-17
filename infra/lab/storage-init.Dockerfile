FROM pgsty/silo:RELEASE.2026-11-12T00-00-00Z@sha256:c20d112390b9a9ce8c11b8af95ad35bcaa62f4759663c09c936cd8d2b511f329
COPY --chmod=0555 storage-init.sh /usr/local/bin/varal-storage-init
COPY storage-policy.json /etc/varal/storage-policy.json
ENTRYPOINT ["/bin/sh", "/usr/local/bin/varal-storage-init"]
