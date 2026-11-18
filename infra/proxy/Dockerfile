# edge (Traefik -> stack) and ssr (Next server -> API) share this image; VARAL_PROXY_ROLE picks one.
FROM nginx:1.30.6-alpine@sha256:901e593c95dc85f5a729f5765516321366ef4ac401821431d408897e95287d0a
COPY edge.conf.template ssr.conf.template /etc/varal/
COPY --chmod=0555 entrypoint.sh /usr/local/bin/varal-proxy
ENTRYPOINT ["/usr/local/bin/varal-proxy"]
