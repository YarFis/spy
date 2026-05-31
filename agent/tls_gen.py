"""
Генерирует самоподписанный TLS сертификат для агента.
Запускать один раз: python tls_gen.py
Создаёт: cert.pem, key.pem
"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime
import ipaddress
import pathlib


def generate(cert_path="cert.pem", key_path="key.pem"):
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "windows32-agent"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256(), default_backend())
    )

    pathlib.Path(key_path).write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption()
        )
    )
    pathlib.Path(cert_path).write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )
    print(f"[+] Сертификат: {cert_path}")
    print(f"[+] Ключ:       {key_path}")


if __name__ == "__main__":
    generate()
