#!/bin/bash
# 生成自签名 SSL 证书（仅用于开发环境）

mkdir -p /etc/nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/selfsigned.key \
  -out /etc/nginx/ssl/selfsigned.crt \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=HL-OS/OU=Dev/CN=localhost"

chmod 600 /etc/nginx/ssl/selfsigned.key
chmod 644 /etc/nginx/ssl/selfsigned.crt

echo "Self-signed certificate generated successfully!"
echo "Key: /etc/nginx/ssl/selfsigned.key"
echo "Cert: /etc/nginx/ssl/selfsigned.crt"
