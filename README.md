# mentos-shop
The project is designed to integrate seamlessly with the Shopify e-commerce platform, providing comprehensive management of user accounts, automated shipping fulfillment, and return management functionalities. The primary goal is to streamline and automate various administrative and logistical tasks associated with managing an online store, thereby reducing manual effort and minimizing errors.
# Installation

## Project setup
- pip3 install -r requirements-base.txt

- python3 cli/cli.py init

- cp .env.example config/.env

- vim config/.env

- python3 cli/cli.py install

### Config nginx
```
server {
        listen 80;
        listen [::]:80;
        server_name test.test.com;
        # HTTP to HTTPS
        # if ($scheme != "https") {
        #     return 301 https://$host$request_uri;

        # }
#       listen 443 ssl http2;
#       listen [::]:443 ssl http2;
#       ssl_certificate "/etc/nginx/cert/fullchain.crt";
#       ssl_certificate_key "/etc/nginx/cert/private.key";
      location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        root /opt/dist;
        index  index.html index.php index.htm;
    }
```
# Contributing
Contributions are very welcome. Please submit bugs and improvement suggestions through issue.
# License
MIT

