ARG PYTHON_VERSION=3.10

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION}
RUN mkdir /opt/mentos_shop_backend
COPY . /opt/mentos_shop_backend
WORKDIR /opt/mentos_shop_backend
RUN apt-get update -y && pip install -r requirements.txt
ENV TZ="Asia/Shanghai" 
COPY config/bot_service.ini /opt/
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
EXPOSE 8000 8000
CMD ["sh","/opt/bot_api/config/docker-entrypoint.sh"]