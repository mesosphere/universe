FROM nginx:1.10.0-alpine

MAINTAINER Mesosphere Support <support@mesosphere.io>

RUN rm -f /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/example_ssl.conf

COPY nginx/ /

COPY target/ /etc/nginx/html

