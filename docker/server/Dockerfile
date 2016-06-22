FROM nginx:1.10.0-alpine

MAINTAINER Mesosphere Support <support@mesosphere.io>

RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/example_ssl.conf

COPY nginx/ /

COPY target/ /etc/nginx/html

RUN  chmod 755 /etc \
  && chmod 755 /etc/nginx \
  && for f in $(find /etc/nginx/html -type f);do chmod 644 $f;done \
  && for d in $(find /etc/nginx/html -type d);do chmod 755 $d;done \
  && ls -alR /etc/nginx/html
