from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

from views import SecurityApi

urlpatterns = patterns('',
    # Examples:
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^api/hello', SecurityApi.as_view()),
    url(r'^callback$', 'views.avans_callback'),
    url(r'^logout$', 'views.avans_logout'),
    url(r'^pull$', 'views.git_pull'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^save$', 'views.save'),
    url(r'^sign$', 'views.sign'),
    url(r'^letsencrypt$', 'views.letsencrypt'),
    url(r'^\.well-known/acme-challenge/(.+)', 'views.letsencrypt_challenge'),
    url(r'^(.*)$', 'views.home', name='home'),
)
