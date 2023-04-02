# define an alias for the specfic python version used in this file.
# define an alias for the specfic python version used in this file.
FROM python:3.10
ENV DJANGO_ENV=prod
RUN mkdir /opt/mentos_shop_backend
COPY . /opt/mentos_shop_backend
WORKDIR /opt/mentos_shop_backend
RUN awk 'BEGIN { cmd="cp -r /opt/mentos_shop_backend/.env.sample /opt/mentos_shop_backend/config/.env"; print "n" |cmd; }'
ENV TZ="Asia/Shanghai"
RUN pip install -r requirements.txt
RUN python manage.py reset_db --noinput
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python mocks/mock_data.py
COPY config/supervisord_mentos.conf /opt/
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
EXPOSE 8000 8000
# VOLUME ["/opt/mentos_shop_backend", "/opt/mentos_shop_backend"]
CMD ["sh","/opt/mentos_shop_backend/config/docker-entrypoint.sh"]