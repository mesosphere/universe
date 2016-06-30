FROM universe-base

COPY http /usr/share/nginx/html/
COPY registry /var/lib/registry/
COPY universe/target/* /usr/share/nginx/html/

RUN chmod 755 /usr/share/nginx/html/ \
  && for f in $(find /usr/share/nginx/html/ -type f);do chmod 644 $f;done \
  && for d in $(find /usr/share/nginx/html/ -type d);do chmod 755 $d;done \
  && ls -alR /usr/share/nginx/html/
