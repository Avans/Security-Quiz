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
import securityquiz.secrets as secrets
import securityquiz.settings as settings

AVANS_KEY = secrets.AVANS_KEY
AVANS_SECRET = secrets.AVANS_SECRET
REQUEST_TOKEN_URL = 'https://publicapi.avans.nl/oauth/request_token?oauth_callback=http://%s/callback'
ACCESS_TOKEN_URL = 'https://publicapi.avans.nl/oauth/access_token'
AUTHORIZE_URL = 'https://publicapi.avans.nl/oauth/saml.php?oauth_token=%s'

consumer = oauth.Consumer(AVANS_KEY, AVANS_SECRET)
client = oauth.Client(consumer)

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
            answer.string = data[key]
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
        answers_dict[answer.question] = answer.string

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
    else:
        return HttpResponseNotFound('404')

    return render(request, template, {'answers': answers_dict})




def sign(request):
    if request.method == 'POST':
        from OpenSSL import crypto
        import time

        ca_cert_file = """-----BEGIN CERTIFICATE-----
MIIFDDCCA/SgAwIBAgIJANgaua7fGCcBMA0GCSqGSIb3DQEBBQUAMIG0MQswCQYD
VQQGEwJVUzEWMBQGA1UECBMNV2FzaGluZ3RvbiBEQzETMBEGA1UEBxMKV2FzaGlu
Z3RvbjEhMB8GA1UEChMYVW5pdGVkIFN0YXRlcyBHb3Zlcm5tZW50MRgwFgYDVQQL
Ew9UaGUgV2hpdGUgSG91c2UxFTATBgNVBAMTDEJhcmFjayBPYmFtYTEkMCIGCSqG
SIb3DQEJARYVYmFyYWNrQHdoaXRlaG91c2UuZ292MB4XDTE0MDUyMTA3MjkxM1oX
DTE0MDYyMDA3MjkxM1owgbQxCzAJBgNVBAYTAlVTMRYwFAYDVQQIEw1XYXNoaW5n
dG9uIERDMRMwEQYDVQQHEwpXYXNoaW5ndG9uMSEwHwYDVQQKExhVbml0ZWQgU3Rh
dGVzIEdvdmVybm1lbnQxGDAWBgNVBAsTD1RoZSBXaGl0ZSBIb3VzZTEVMBMGA1UE
AxMMQmFyYWNrIE9iYW1hMSQwIgYJKoZIhvcNAQkBFhViYXJhY2tAd2hpdGVob3Vz
ZS5nb3YwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC6Lqnt0bLHvJAb
LOVR4FEhLgAf4jT/MiJ/Oe8Hbo5Z1LaA/6bcAm8UDYdzlg+NcWyuZv1Pwm5BWSpK
T6z394a4kYUSs/Kwq+HAY8SPt1AZUx4cD0p4D8PAYKDLYAv1PwvMIOnpIscSIrhO
Znug5RGC5B+1flarKBedcCQ744Xrt2FJN4zwUJXSPg1BUHs36Q6tfZyjH2rai8xY
q/kmkFwxj/Hsax7nCS8VALOBB2drySTMQMpLDt3t604xIKvO4oLOPo/KkxxiHgNm
FM0V4aSY1URKBT/4a98YU4rbYe9HsicN2b23VdDOJNpR3xoBnqcDeUmeOyr+u9yC
xMfmWAO9AgMBAAGjggEdMIIBGTAdBgNVHQ4EFgQUHQ/Wns26nFHViXFiQPoJdHAh
/YYwgekGA1UdIwSB4TCB3oAUHQ/Wns26nFHViXFiQPoJdHAh/YahgbqkgbcwgbQx
CzAJBgNVBAYTAlVTMRYwFAYDVQQIEw1XYXNoaW5ndG9uIERDMRMwEQYDVQQHEwpX
YXNoaW5ndG9uMSEwHwYDVQQKExhVbml0ZWQgU3RhdGVzIEdvdmVybm1lbnQxGDAW
BgNVBAsTD1RoZSBXaGl0ZSBIb3VzZTEVMBMGA1UEAxMMQmFyYWNrIE9iYW1hMSQw
IgYJKoZIhvcNAQkBFhViYXJhY2tAd2hpdGVob3VzZS5nb3aCCQDYGrmu3xgnATAM
BgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4IBAQAsPNGb/voHkeLEb4xjVw0d
ezdajGxxhf+b3fRZecDuyoNS/cKwpfOtoEPo9PmnCYOLqZiFVkH2zgfAjVRZXWQw
/v3T8JtidGZzRXCmElZO8NEzflfhVa8qc/CRpmQ1SQhLjcTU8XJD02uMf7LS3pzj
CqHy+aX3fHbotHlqB1nkFZwoiAdTX5z7e4znsV9iElHEXjVtGVpbQRxe45IN2yhC
w2m6uzir1Ozsm6cpsxxygziZluz8t7QDyyfi8GkDtdk4joLKsAeawwxjm4JlDi96
jluZ6JUN8TeifPsCWsee5U3XtykclfVDw7DyfgEq9xGFBFoI1wuUfUxmoszGgTvc
-----END CERTIFICATE-----
"""
        ca_key_file = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAui6p7dGyx7yQGyzlUeBRIS4AH+I0/zIifznvB26OWdS2gP+m
3AJvFA2Hc5YPjXFsrmb9T8JuQVkqSk+s9/eGuJGFErPysKvhwGPEj7dQGVMeHA9K
eA/DwGCgy2AL9T8LzCDp6SLHEiK4TmZ7oOURguQftX5WqygXnXAkO+OF67dhSTeM
8FCV0j4NQVB7N+kOrX2cox9q2ovMWKv5JpBcMY/x7Gse5wkvFQCzgQdna8kkzEDK
Sw7d7etOMSCrzuKCzj6PypMcYh4DZhTNFeGkmNVESgU/+GvfGFOK22HvR7InDdm9
t1XQziTaUd8aAZ6nA3lJnjsq/rvcgsTH5lgDvQIDAQABAoIBAFgRKqAryP1h3Gh+
XBrWmImxUK3EOn1cIaU8qixBx2QGki2CwFLhc9lwbNnn6YNmW5pDbR8FQVH382Ej
PxYsJ7W2X9Pw+qNHKonup1OzylewUVXEhd0018tv6Z9J114ybEoqZ3q30KJrefLb
1y7MK/RWJAmdsTFUzZbTLNCHVxmf3gL05K/H0USY19+sO2GkhHIU9dYrafywAlPh
iFuZAvcVIUDhKsowslBYD3+R5yamN6bvWy8E1IbOBM76nMQKcJlpQv7T+mCJUWhW
71niSoXS8AoxEgbJftZtfqo5Cp5ZenAMUaje4QqjLcqvda41baU3uAIAdadgt/oq
lVl+EaECgYEA2qWLoBYH87xd0MMeYPznDH3Na041c4DNmA5ZT2aaDn88+to9dyrR
Ur052VOz6zMnHd4MWlUvaTpEjUKsxENLwajI8PtQVlB1Kio8Mn5rMdW/A1NUDeDm
db8OTLYxGWw3ug/m6/p7xTepHvJHWAJh4I9iNA+jYZkc3ppWDEbOJfMCgYEA2f1M
EYvDCsLhpx3n4wSjOMRjS1XUGPn/v5aYdVF9rnr2E1zxgZaZRMhD2P2umUj4+2SI
2a1Ve99uXuqgM+1OC5G5TNKje3HikqnGTnqDS2L76WLDuZdkmNmIMKuibSZteHl/
2llrkdGCmV4pfjvszilCxph/rQ5+0uBJFIMrK48CgYEAztD+ZJvSQ8vulbSqvKUc
S+WHdDPTPYEdd/JCqmdr28ChRss+jsUSoQfae2bAbf7Bxm+uEZg4M3npNBFYaIEb
XICyKbgegrayTQMMU9revJHpj1S30jTk6YWiGg/QG7MQd0/pZ1dU0fTXZS1ZLLd8
K7SU+Je+PGhfNXSZZh1ni98CgYArbiS2pjLAtR0CD5pAh48BY1cpDjuIkl5azGUp
kofIuGTIbM8M83Ur1/50f+5GSdyZMWl2fOs4F8bEkFhEoDXZZjoVzS2XDZSHhd2l
ixEXduwbjnrSQhBfx48zqy5cMrjCtOo9FW2yCpzLc5Auvz+pv1y3dnCRiP7Jgrfs
p0l1jwKBgQCYUOEr7FlXMas0KVXzvR4bg1c6pEuORhkdP3w/IO+88RflPe/or1c6
M15u8GjRELX7QyUx5x3fPnYDVPJ97FDqjhHcSiq8Tu8bvFsoBxyZu1EfbMY+ndB7
ojEMEyKAGuYrWFU0GvmNGYeIOdl7Xc7hYgU5m9VzovCV7rs3CIy3xQ==
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
        signed_cert.sign(ca_key, 'sha1')

        response = HttpResponse(crypto.dump_certificate(crypto.FILETYPE_PEM, signed_cert), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=signed-certificaat.pem'
        return response

    return render(request, 'sign.html')