from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from quiz.models import Answer
import oauth2 as oauth, cgi, json, base64, urlparse, subprocess
from oauth2_provider.views.generic import ProtectedResourceView
import securityquiz.secrets as secrets
import securityquiz.settings as settings
import datetime, pytz

AVANS_KEY = secrets.AVANS_KEY
AVANS_SECRET = secrets.AVANS_SECRET
REQUEST_TOKEN_URL = 'https://publicapi.avans.nl/oauth/request_token?oauth_callback=http://%s/callback'
ACCESS_TOKEN_URL = 'https://publicapi.avans.nl/oauth/access_token'
AUTHORIZE_URL = 'https://publicapi.avans.nl/oauth/saml.php?oauth_token=%s'

consumer = oauth.Consumer(AVANS_KEY, AVANS_SECRET)
client = oauth.Client(consumer)

@csrf_exempt
def git_pull(request):
    output = subprocess.check_output(["git", "-C", "/var/www/sec1.aii.avans.nl", "pull"])
    return HttpResponse(output)

def avans_login(request):

    resp, content = client.request(REQUEST_TOKEN_URL % request.get_host(), "GET")

    if resp['status'] != '200':
        raise Exception("Invalid response from oauth")

    request.session['request_token'] = dict(cgi.parse_qsl(content))

    url = AUTHORIZE_URL % (request.session['request_token']['oauth_token'])
    return HttpResponseRedirect(url)

def avans_callback(request):
    token = oauth.Token(request.session['request_token']['oauth_token'], request.session['request_token']['oauth_token_secret'])
    token.set_verifier(request.GET['oauth_verifier'])

    client = oauth.Client(consumer, token)

    resp, content = client.request(ACCESS_TOKEN_URL, "GET")
    if resp['status'] != '200':
        raise Exception("Invalid response from Avans.")

    access_token = dict(cgi.parse_qsl(content))
    token = oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret'])
    client = oauth.Client(consumer, token)

    resp, content = client.request('https://publicapi.avans.nl/oauth/studentnummer/', 'GET')
    data = json.loads(content)[0]
    studentnummer = data['studentnummer']
    inlognaam = data['inlognaam']

    try:
        user = User.objects.get(username=inlognaam)
    except User.DoesNotExist:
        user = User.objects.create_user(inlognaam, studentnummer, 'secret')

    user = authenticate(username=inlognaam, password='secret')
    login(request, user)

    return HttpResponseRedirect('/')

def avans_logout(request):
    logout(request)
    return HttpResponse('Je bent nu uitgelogd... <a href="/">Opnieuw inloggen</a>')

@csrf_exempt
def save(request):
    data = dict(urlparse.parse_qsl(base64.b64decode(request.body), True))
    print data
    save_data(data, request.user)
    return HttpResponse('ok')

def save_data(data, user):
    for key in data:
        if key.startswith('answer'):
            answer, created = Answer.objects.get_or_create(user=user, question=key)
            if answer.string <> data[key]:
                answer.string = data[key]
                answer.submitted = pytz.utc.localize(datetime.datetime.utcnow())
                answer.points = None
                answer.comment = None
                answer.save()

def home(request, url):
    if not request.user.is_authenticated():
        return avans_login(request)

    if request.method == 'POST':
        save_data(request.POST, request.user)

        messages.add_message(request, messages.INFO, 'Je antwoorden zijn opgeslagen')
        return HttpResponseRedirect('/' + url)

    answers = Answer.objects.filter(user=request.user)
    answers_dict = {}
    for answer in answers:

        answers_dict[answer.question] = {'string': answer.string, 'points': answer.points}

    if url == 'sql' or url == '':
        template = 'sql.html'
    elif url == 'xss':
        template = 'xss.html'
    elif url == 'path':
        template = 'path.html'
    elif url == 'wachtwoorden':
        template = 'wachtwoorden.html'
    elif url == 'openssl':
        template = 'openssl.html'
    elif url == 'bonus':
        template = 'bonus.html'
    elif url == 'oauth':
        template = 'oauth.html'
    else:
        return HttpResponseNotFound('404')

    return render(request, template, {'answers': answers_dict})


class SecurityApi(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Geheime code: abguvatgbfrrurerzbirnybat")

def sign(request):
    if request.method == 'POST':
        from OpenSSL import crypto
        import time

        ca_cert_file = """-----BEGIN CERTIFICATE-----
MIIEjzCCA3egAwIBAgIJAIyZIB4fbN2mMA0GCSqGSIb3DQEBCwUAMIGLMQswCQYD
VQQGEwJVUzETMBEGA1UECBMKQ2FsaWZvcm5pYTEUMBIGA1UEBxMLTG9zIEFuZ2Vs
ZXMxDzANBgNVBAoTBlNwYWNlWDEMMAoGA1UECxMDQ0VPMRIwEAYDVQQDEwlFbG9u
IE11c2sxHjAcBgkqhkiG9w0BCQEWD2Vsb25Ac3BhY2V4LmNvbTAeFw0xNTA1Mjgx
NjEyMjFaFw0yNTA1MjUxNjEyMjFaMIGLMQswCQYDVQQGEwJVUzETMBEGA1UECBMK
Q2FsaWZvcm5pYTEUMBIGA1UEBxMLTG9zIEFuZ2VsZXMxDzANBgNVBAoTBlNwYWNl
WDEMMAoGA1UECxMDQ0VPMRIwEAYDVQQDEwlFbG9uIE11c2sxHjAcBgkqhkiG9w0B
CQEWD2Vsb25Ac3BhY2V4LmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC
ggEBAMWr64mMZDfWUuYmROz+FszmwjGZvFz0CGxiExHEAFfzZfF60Rts2Qm+o7cc
bZ/UtAaIgIve5WiWhQ5mqDoyECfuVOTcddWCrskLgLafoP6nPVdTDIXsPtsjtRuV
D1ptsduDVCeQkcKFUcfLd6QXJaOAYU20gb7FJ8KFUmJXn4HXg6BsZvu8grJgh51O
29JRw83I0FxzBZw4JSvETW968NexO+aliR/inK4GQQqk4joxuT6MSVsd+17ss6wn
WO1nUNxhSW3MQePrfphkQbNZn/l1T1MfN6XAs4P9boqgENHZ2WskGIeZ5g1I4MVE
WPFTZ8HwprCvybM8mneqVp/P+FcCAwEAAaOB8zCB8DAdBgNVHQ4EFgQUHvGJ8tZM
owfGFNeyuhsYq8JN/o8wgcAGA1UdIwSBuDCBtYAUHvGJ8tZMowfGFNeyuhsYq8JN
/o+hgZGkgY4wgYsxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRQw
EgYDVQQHEwtMb3MgQW5nZWxlczEPMA0GA1UEChMGU3BhY2VYMQwwCgYDVQQLEwND
RU8xEjAQBgNVBAMTCUVsb24gTXVzazEeMBwGCSqGSIb3DQEJARYPZWxvbkBzcGFj
ZXguY29tggkAjJkgHh9s3aYwDAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQsFAAOC
AQEAfe9TXLrrwA/3xf85HB+i7CxaFNTmWZvsN2Ico9Ks1/Dt7eAB61ghHFIxCqHz
LQGa77wFAI5kgzv3TembXV1kHz4pGigPC6EkNEh0Kc2O3fwz6CryK7/OrjkElKEn
ti/9loLr8+rhQKF0c2NS3qiAoYsR/kkdBZ+niT+yXCIekpQNybfDT8WqDm4Rv2s+
u/6pZa7zZLLlORpxnuFfjjo+n/06b4+xHn+xvyGWijMcOqZdyhU0UjZ7OAW/ZEQp
3uvp8fso+Esov+Abl0Lxtr/Gk7utH/h0AD6vWJJwDlS65uqKBeuIOUoCAHy3oPH5
p+BxtuhS2Lv5g2jHRgIxVt22rg==
-----END CERTIFICATE-----
"""
        ca_key_file = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAxavriYxkN9ZS5iZE7P4WzObCMZm8XPQIbGITEcQAV/Nl8XrR
G2zZCb6jtxxtn9S0BoiAi97laJaFDmaoOjIQJ+5U5Nx11YKuyQuAtp+g/qc9V1MM
hew+2yO1G5UPWm2x24NUJ5CRwoVRx8t3pBclo4BhTbSBvsUnwoVSYlefgdeDoGxm
+7yCsmCHnU7b0lHDzcjQXHMFnDglK8RNb3rw17E75qWJH+KcrgZBCqTiOjG5PoxJ
Wx37XuyzrCdY7WdQ3GFJbcxB4+t+mGRBs1mf+XVPUx83pcCzg/1uiqAQ0dnZayQY
h5nmDUjgxURY8VNnwfCmsK/Jszyad6pWn8/4VwIDAQABAoIBAHkzyOA17N0v1PS5
UlneEizg8QFouk5kcyXBnN+vxmYnH8LJA55FR27qLYgBLlZqHVhEKk2ZBiDy6fLC
jzPfrnhNclBBvR6FWpZ7LxjLF/QMp1f73BnhmUjUxB99bkSMLhnilJ8NzdHv3Q0c
fOdoKfPuq7rxivxl9tMW3ETgZTU+0dSeJH8ZkkcQblckNpqP//oWFpXYrgftgyR3
kM+uZya2kwaZ15XC2O1IXbvFVjppw4z/z8KMBc6azGrSFJ6xGkve+1KKBuVQ1Vpg
sFXBaKHoVG5NpGiwiBkbERkn1Jp+lgJkstDyzGtIVmhzT7g5+YIvXE5uWU/NVRDp
0n8n6UECgYEA/hgkUfJ/uVlORhkIyW+thG9VPO1k35BdOjw5f7xDN6DSyYNSRubi
q6F3KWW807fEubGYzXaTh5QCB9z+gUuVAtjo9Mb0RPBEyWwXFi0ynxLzNQxA692U
Id67JHVPK4gsgP7jZi8+pAbN3xSfRG1BXdsp+RUJdWNiaLeWOsHI+bMCgYEAxydy
enmg+dzz8qz6my9G9uH0dqoG8BHlwPp7h/vmSbhWAD4+BIGCHbGt2zk/Zh7w6PsQ
9nMrWSwAkStdpW0WLz/oNIijVN8dInlFnB3qq6o1t0Jrz2K4ngUN1PAA19Ft1s+r
VZpSM+uKViKKuthORNeVM0D3D3gfrisdAZAV7M0CgYBguef5mgqtECYP4S/LHsw7
Afa8vtILmPUkWhC5Y31jC8GyHF+Rxgq7szeddrEvF2G4HrdAX8dBcUJko+fuaEtN
Ti1AIQyTwbMtygvv0TzX+WrD4upD35GoYxVyh4Wf2LK4WE9QcuOxpTVxmnQWpFCh
3fBYdX2oRjEME/cIXwSWqQKBgEpc0WMn/VKvDSvlKSI+8fmHf3e7nyGPHUIEhZHO
HjwSp5Ipq5CVJxedW7SK2MBx9zSXYssTT/FY+9E45xu48tqruzG6f3pWYROZQsO7
a/+za6FFHOpwC019x59mCnqLib73BhvNproaTipBdZm04OzVrrFXpajSCspG8Oq/
eWBVAoGACI+4ROdYWCprQRgH2Qr5nKnRkN1mZzBl4hgodSGCZa3TWnBVHtXacluF
KJ8dp3ZgjiQ9aQujFD5oPnmSJ8wvJijF8ngEFw60+axRrWnUmejWkrexA1Hlv0Er
tq9DcELddZK2gJXaXpL1wOL+Ex5RzzRmjqKmmkkn1//ikn+nrZU=
-----END RSA PRIVATE KEY-----
"""
        csr = crypto.load_certificate_request(crypto.FILETYPE_PEM, request.FILES['csr'].read())
        ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, ca_cert_file)
        ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, ca_key_file)

        signed_cert = crypto.X509()
        signed_cert.set_serial_number(1)
        signed_cert.gmtime_adj_notBefore(0)
        signed_cert.gmtime_adj_notAfter(60 * 60 * 24 * 365 * 5)
        signed_cert.set_issuer(ca_cert.get_subject())
        signed_cert.set_subject(csr.get_subject())
        signed_cert.set_pubkey(csr.get_pubkey())
        signed_cert.sign(ca_key, 'sha256')

        response = HttpResponse(crypto.dump_certificate(crypto.FILETYPE_PEM, signed_cert), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=signed-certificaat.crt'
        return response

    return render(request, 'sign.html')