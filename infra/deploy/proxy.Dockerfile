FROM nginx:1.30.6-alpine@sha256:901e593c95dc85f5a729f5765516321366ef4ac401821431d408897e95287d0a
COPY infra/deploy/edge.conf.template infra/deploy/ssr.conf.template /etc/varal/
COPY --chmod=0555 infra/deploy/proxy-entrypoint.sh /usr/local/bin/varal-proxy
ENTRYPOINT ["/usr/local/bin/varal-proxy"]
