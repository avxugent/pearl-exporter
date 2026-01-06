ARG ARCH="amd64"
ARG OS="linux"
FROM --platform=$BUILDPLATFORM quay.io/prometheus/busybox:latest 
LABEL maintainer="Kristof Keppens <kristof.keppens@ugent.be>"

COPY .build/linux-amd64/pearl-exporter  /bin/pearl-exporter

EXPOSE      9115
ENTRYPOINT  [ "/bin/pearl-exporter" ]
