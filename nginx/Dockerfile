FROM ubuntu:xenial-20181113

RUN apt-get update && apt-get install -y nginx
COPY default /etc/nginx/sites-available/

COPY site /site

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

VOLUME /static

CMD [ "nginx", "-g", "daemon off;" ]