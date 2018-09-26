from OpenSSL import crypto
from os.path import exists, join
import ipgetter


def create(name):
    name_key = "{}.key".format(name)
    name_cert = "{}.crt".format(name)

    cakey = createKeyPair(crypto.TYPE_RSA, 2048)
    careq = createCertRequest(cakey, CN='Certificate Authority')
    cacert = createCertificate(careq, (careq, cakey), 0, (0, 60*60*24*365*10))  # CA certificate is valid for 10 years

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "."
    cert.get_subject().ST = "."
    cert.get_subject().L = "."
    cert.get_subject().O = "."
    cert.get_subject().OU = "."
    ip = ipgetter.myip()
    print(ip)
    cert.get_subject().CN = ip
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(60*60*24*365*10)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(cakey)
    cert.sign(cakey, 'sha256')

    print('Creating Certificate Authority private key in {}'.format(name_key))
    with open(name_key, 'w') as capkey:
        capkey.write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, cakey).decode('utf-8')
        )

    print('Creating Certificate Authority certificate in {}'.format(name_cert))
    with open(name_cert, 'w') as ca:
        ca.write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cacert).decode('utf-8')
        )

    print('done with certs')


def createKeyPair(type, bits):
    """
    Create a public/private key pair.
    Arguments: type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey


def createCertRequest(pkey, digest="sha256", **name):
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is sha256
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    subj = req.get_subject()

    for key, value in name.items():
        setattr(subj, key, value)

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req


def createCertificate(req, issuerCertKey, serial, validityPeriod,
                      digest="sha256"):
    """
    Generate a certificate given a certificate request.
    Arguments: req        - Certificate request to use
               issuerCert - The certificate of the issuer
               issuerKey  - The private key of the issuer
               serial     - Serial number for the certificate
               notBefore  - Timestamp (relative to now) when the certificate
                            starts being valid
               notAfter   - Timestamp (relative to now) when the certificate
                            stops being valid
               digest     - Digest method to use for signing, default is sha256
    Returns:   The signed certificate in an X509 object
    """
    issuerCert, issuerKey = issuerCertKey
    notBefore, notAfter = validityPeriod
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert



def create_self_signed_cert(cert_dir, name):
    """
    If datacard.crt and datacard.key don't exist in cert_dir, create a new
    self-signed cert and keypair and write them into that directory.
    """
    
    cert_file = "{}.crt".format(name)
    key_file = "{}.key".format(name)
    
    if not exists(join(cert_dir, cert_file)) \
            or not exists(join(cert_dir, key_file)):

        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "Minnesota"
        cert.get_subject().L = "Minnetonka"
        cert.get_subject().O = "my company"
        cert.get_subject().OU = "my organization"
        # cert.get_subject().CN = gethostname()
        ip = ipgetter.myip()
        cert.get_subject().CN = ip
        print(ip)

        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        open(join(cert_dir, cert_file), "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(join(cert_dir, key_file), "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

        print("generated!")
