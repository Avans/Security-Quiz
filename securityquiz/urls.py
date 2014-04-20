from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'views.home', name='home'),
    url(r'^callback$', 'views.avans_callback'),
    url(r'^logout$', 'views.avans_logout'),
    url(r'^pull$', 'views.pull'),
    url(r'^admin/', include(admin.site.urls)),
)
