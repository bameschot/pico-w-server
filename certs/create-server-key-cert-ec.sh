openssl ecparam -name prime256v1 -genkey -noout -out ec_key.der -outform DER
openssl req -new -x509 -key ec_key.der -out ec_cert.der -outform DER -days 9999 -nodes