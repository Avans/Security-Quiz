from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from quiz.models import Answer
import oauth2 as oauth, cgi, json, base64, urlparse
import securityquiz.secrets as secrets
import securityquiz.settings as settings

AVANS_KEY = secrets.AVANS_KEY
AVANS_SECRET = secrets.AVANS_SECRET
REQUEST_TOKEN_URL = 'https://publicapi.avans.nl/oauth/request_token?oauth_callback=http://%s/callback'
ACCESS_TOKEN_URL = 'https://publicapi.avans.nl/oauth/access_token'
AUTHORIZE_URL = 'https://publicapi.avans.nl/oauth/saml.php?oauth_token=%s'

consumer = oauth.Consumer(AVANS_KEY, AVANS_SECRET)
client = oauth.Client(consumer)

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
    else:
        return HttpResponseNotFound('404')

    return render(request, template, {'answers': answers_dict})
