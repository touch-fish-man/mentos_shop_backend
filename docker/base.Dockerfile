FROM python:3.10
RUN mkdir /opt/mentos_shop_backend
COPY . /opt/mentos_shop_backend
WORKDIR /opt/mentos_shop_backend
ENV DJANGO_ENV=prod
RUN awk 'BEGIN { cmd="cp -r /opt/mentos_shop_backend/.env.sample /opt/mentos_shop_backend/config/.env"; print "n" |cmd; }'
ENV TZ="UTC"
ENV DJANDO_ENV="pord"
RUN pip install -r requirements.txt
# RUN python manage.py reset_db -c --noinput
RUN python manage.py makemigrations
RUN python manage.py migrate

COPY config/supervisord_mentos.conf /opt/
RUN chmod -R a+x /opt/mentos_shop_backend/config
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
RUN python /opt/mentos_shop_backend/mocks/init_data.py