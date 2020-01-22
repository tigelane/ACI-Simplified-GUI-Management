import pathlib
import subprocess

bind = "0.0.0.0:5000"
accesslog = "-"
errorlog = "-"
workers = "10"
secure_scheme_headers = {'X-FORWARDED-PROTOCOL': 'ssl',
                         'X-FORWARDED-PROTO': 'https',
                         'X-FORWARDED-SSL': 'on'}

cert_path = pathlib.Path('cert.pem')
key_path = pathlib.Path('key.pem')

if not all([cert_path.exists(), key_path.exists()]):
    command = ['openssl', 'req', '-x509', '-newkey',
               'rsa:4096', '-nodes', '-out', 'cert.pem',
               '-keyout', 'key.pem', '-days', '365', '-subj',
               '/C=US/ST=Portland/L=Oregon/O=IGNW/OU=Solutions/CN=localhost']

    out = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    print(out)

certfile = "cert.pem"
keyfile = "key.pem"
