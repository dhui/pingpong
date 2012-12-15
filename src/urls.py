from django.conf.urls import patterns, include, url

from src.pingpong import views as pingpong_views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
                       url(r"^$", pingpong_views.index),
                       url(r"^matches/$", pingpong_views.Matches.as_view(), name="matches"),
                       url(r"^player_matches/(?P<player_id>\d+)/$", pingpong_views.player_matches),
                       url(r"^players/$", pingpong_views.Players.as_view(), name="players"),
    # Examples:
    # url(r'^$', 'pingpong.views.home', name='home'),
    # url(r'^pingpong/', include('pingpong.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
