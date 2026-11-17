# QA-only image: its build context contains only the public ephemeral lab CA.
FROM varal11-browser-lab:node22
USER root
COPY ca.pem /usr/local/share/ca-certificates/varal-lab.crt
RUN update-ca-certificates
USER 1001:1001
