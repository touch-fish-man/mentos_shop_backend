ARG PYTHON_VERSION=3.10

# define an alias for the specfic python version used in this file.
FROM python:${PYTHON_VERSION}
RUN mkdir /opt/mentos_shop_backend
COPY . /opt/mentos_shop_backend
COPY .env.example /opt/mentos_shop_backend/.env
WORKDIR /opt/mentos_shop_backend
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
ENV TZ="Asia/Shanghai" 
COPY config/supervisord_mentos.conf /opt/
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
EXPOSE 8000 8000
VOLUME ["/opt/mentos_shop_backend", "/opt/mentos_shop_backend"]
CMD ["sh","/opt/mentos_shop_backend/config/docker-entrypoint.sh"]