# Public files, read-only. One route per PUBLIC bucket (see object-storage/buckets.conf).
# Private buckets (courier-receipts, shipment-documents) have no route here, on purpose.

# Product photos and other public product files: /media/products/<key>
location /media/products/ {
    limit_except GET HEAD { deny all; }
    set $s3 http://object-storage:8333;
    rewrite ^/media/products/(.*)$ /product-media/$1 break;
    proxy_pass $s3;
    proxy_set_header Host object-storage:8333;
    proxy_hide_header Set-Cookie;
    expires 7d;
}

# Profile pictures: /media/avatars/<key>
location /media/avatars/ {
    limit_except GET HEAD { deny all; }
    set $s3 http://object-storage:8333;
    rewrite ^/media/avatars/(.*)$ /user-avatars/$1 break;
    proxy_pass $s3;
    proxy_set_header Host object-storage:8333;
    proxy_hide_header Set-Cookie;
    expires 7d;
}
