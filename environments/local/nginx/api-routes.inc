# API routes, included by both sites in default.conf (LOCAL environment).
#
# Each route tries the CONTAINER first. If the container is stopped, Nginx gets an error
# (502/504) and falls back to the copy you run in IntelliJ on the same port.
# So: "docker compose stop order-service" + run it in IntelliJ = no config change needed.
#
# "set $u ...; proxy_pass $u;" makes Nginx look up the container name per request
# (with the resolver in default.conf), so Nginx starts even when a container is missing.

location /api/v1/user/          { set $u http://user-service:8080;         proxy_pass $u; error_page 502 504 = @user_ide; }
location /oauth2/               { set $u http://user-service:8080;         proxy_pass $u; error_page 502 504 = @user_ide; }
location /login/oauth2/         { set $u http://user-service:8080;         proxy_pass $u; error_page 502 504 = @user_ide; }
location /api/v1/product/       { set $u http://product-service:8081;      proxy_pass $u; error_page 502 504 = @product_ide; }
location /api/v1/order/         { set $u http://order-service:8082;        proxy_pass $u; error_page 502 504 = @order_ide; }
location /api/v1/notification/  { set $u http://notification-service:8083; proxy_pass $u; error_page 502 504 = @notification_ide; }
location /api/v1/payment/       { set $u http://payment-service:8084;      proxy_pass $u; error_page 502 504 = @payment_ide; }
# Paths starting with /internal/ have no route on purpose. Only services call them.

location @user_ide         { proxy_pass http://host.docker.internal:8080; }
location @product_ide      { proxy_pass http://host.docker.internal:8081; }
location @order_ide        { proxy_pass http://host.docker.internal:8082; }
location @notification_ide { proxy_pass http://host.docker.internal:8083; }
location @payment_ide      { proxy_pass http://host.docker.internal:8084; }
