# Headers sent to every service. Included by both sites in default.conf.
proxy_set_header Host              $http_host;
proxy_set_header X-Real-IP         $remote_addr;
# Overwrite, never append: a client must not be able to fake its IP (rate limits).
proxy_set_header X-Forwarded-For   $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host  $http_host;
proxy_set_header X-Request-Id      $request_id;

client_max_body_size 10m;   # photo and PDF uploads
