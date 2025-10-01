---
Created Date: 2025-09-30
Created Time: 09:09:90
---

## 1) Create your own CA (Certificate Authority)

Run these in a terminal (replace filenames as desired):

### CA private key

```bash
openssl genrsa -out ca.key 4096
```

### Self-signed CA certificate (valid 3 years here)

```bash
openssl req -x509 -new -nodes -key ca.key -sha256 -days 1095 -out ca.pem -subj "//CN=MyLocalCA"
```

`ca.pem` is your CA certificate (public). `ca.key` is the private CA key (keep secret).

## 2) Create server certificate with SAN (include your PC IP)

Create a file `server.cnf` with this content (replace `192.168.1.50` with your PC IP):

```ini
[req]
default_bits        = 2048
prompt              = no
default_md          = sha256
distinguished_name  = dn
req_extensions      = req_ext

[dn]
CN = 192.168.1.50

[req_ext]
subjectAltName = @alt_names

[alt_names]
IP.1 = 192.168.1.50
```

Then run:

### Server private key

```bash
openssl genrsa -out server.key 2048
```

### CSR using the config (includes SAN)

```bash
openssl req -new -key server.key -out server.csr -config server.cnf
```

### Sign server CSR with your CA

```bash
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \-out server.crt -days 365 -sha256 -extfile server.cnf -extensions req_ext
```

You now have `server.crt` and `server.key` (use them on the Flask server) and `ca.pem` (trusted CA).

## 3) Create a client certificate (for [MacroDroid](https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid&hl=en))

Create a client key+CSR and sign it with your CA:

### Client private key

```bash
openssl genrsa -out client.key 2048
```

### Client CSR (CN can be anything)

```bash
openssl req -new -key client.key -out client.csr -subj "//CN=MacroDroidPhone"
```

### Sign CSR with the CA

```bash
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca.key -CAcreateserial \-out client.crt -days 365 -sha256
```

Now you have `client.crt` and `client.key`.

## 4) Export client cert & key to a `.p12` (PKCS#12) for [MacroDroid](https://play.google.com/store/apps/details?id=com.arlosoft.macrodroid&hl=en)

MacroDroid expects a `.p12/.pfx` or JKS. Export:![[MacroDroid Client Certificate (mTLS).png]]

```bash
openssl pkcs12 -export \
  -inkey client.key \
  -in client.crt \
  -certfile ca.pem \
  -out client.p12 \
  -name "MacroDroidClient"
```

> [!important]+
> You will be prompted to set an export password, **remember it**. This is the password you’ll enter in MacroDroid when selecting the certificate.

Copy `client.p12` to your phone (USB, cloud, email, or file share).
