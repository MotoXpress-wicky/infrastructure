# API routes for STAGING, included by both sites. Containers only.
location /api/v1/user/          { set $u http://user-service:8080;         proxy_pass $u; }
location /oauth2/               { set $u http://user-service:8080;         proxy_pass $u; }
location /login/oauth2/         { set $u http://user-service:8080;         proxy_pass $u; }
location /api/v1/product/       { set $u http://product-service:8081;      proxy_pass $u; }
location /api/v1/order/         { set $u http://order-service:8082;        proxy_pass $u; }
location /api/v1/notification/  { set $u http://notification-service:8083; proxy_pass $u; }
location /api/v1/payment/       { set $u http://payment-service:8084;      proxy_pass $u; }
# Paths starting with /internal/ have no route on purpose. Only services call them.
