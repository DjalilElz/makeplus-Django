from django.urls import path

from . import views

app_name = 'webapp'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('manifest.json', views.manifest_json, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),

    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('select-event/', views.select_event_view, name='select_event'),
    path('install/', views.install_view, name='install'),

    path('participant/home/', views.participant_home_view, name='participant_home'),
    path('participant/program/', views.participant_program_view, name='participant_program'),
    path('participant/guide/', views.participant_guide_view, name='participant_guide'),
    path('participant/announcements/', views.participant_announcements_view, name='participant_announcements'),
    path('participant/profile/', views.participant_profile_view, name='participant_profile'),

    path('controller/home/', views.controller_home_view, name='controller_home'),
    path('controller/program/', views.controller_program_view, name='controller_program'),
    path('controller/announcements/', views.controller_announcements_view, name='controller_announcements'),
    path('controller/profile/', views.controller_profile_view, name='controller_profile'),
    path('controller/statistics/', views.controller_statistics_view, name='controller_statistics'),
    path('controller/scanner/', views.controller_scanner_view, name='controller_scanner'),
]
