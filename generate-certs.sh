#!/usr/bin/env bash
set -e

# Go into project root
cd "$(dirname "$0")"

# Make a clean certs folder
rm -rf certs
mkdir certs
cd certs

# Ask user for IP to include in SAN
read -rp "Enter the server IP address (default: 192.168.1.50): " SERVER_IP
SERVER_IP=${SERVER_IP:-192.168.1.50}

echo "📌 Creating server.cnf with SANs..."
cat > server.cnf <<EOF
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
req_extensions     = req_ext
distinguished_name = dn

[ dn ]
CN = ${SERVER_IP}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
IP.1    = ${SERVER_IP}
EOF

echo "📌 Generating CA..."
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 1095 -out ca.pem -subj "//CN=MyLocalCA"

echo "📌 Generating server certificate..."
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -config server.cnf
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \-out server.crt -days 365 -sha256 -extfile server.cnf -extensions req_ext

echo "📌 Generating client certificate..."
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "//CN=MacroDroidPhone"
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial \-out client.crt -days 365 -sha256

echo "📌 Packaging client certificate into PKCS#12 (.p12)..."
# You will be asked for a password here (same one you use in MacroDroid)
openssl pkcs12 -export -inkey client.key -in client.crt -certfile ca.pem -out client.p12 -name "MacroDroidClient"

echo "✅ All certificates generated in ./certs/"
echo "   - Using IP: ${SERVER_IP}"
