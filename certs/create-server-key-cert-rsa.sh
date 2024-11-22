openssl req -x509 -newkey rsa:4096 -nodes -out rsa_cert.pem -keyout rsa_key.pem -days 365
openssl pkey -in rsa_key.pem -out rsa_key.der -outform DER
openssl x509 -in rsa_cert.pem -out rsa_cert.der -outform DER