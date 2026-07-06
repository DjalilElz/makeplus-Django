from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView  # Add this
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from events.serializers import CustomTokenObtainPairView
from dashboard.views import public_form_view
from dashboard.views_eposter_public import public_eposter_form_view
from dashboard.views_eposter_final import eposter_final_submission_form, communication_orale_final_submission_form, eposter_public_gallery

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="MakePlus API",
        default_version='v1',
        description="MakePlus Event Management API Documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@makeplus.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Root redirect to API or Swagger
    path('', RedirectView.as_view(url='/swagger/', permanent=False), name='index'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # JWT Authentication
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API Endpoints
    path('api/', include('events.urls')),
    
    # Dashboard (Admin Panel)
    path('dashboard/', include('dashboard.urls')),
    
    # Email and Form Tracking
    path('track/', include('dashboard.urls_tracking')),
    
    # Public Forms
    path('forms/<slug:slug>/', public_form_view, name='public_form'),
    
    # Public Scientific Contribution Submission Form
    path('contributions/<uuid:event_id>/', public_eposter_form_view, name='public_contribution_form'),
    # Legacy URL redirect
    path('eposter/<uuid:event_id>/', public_eposter_form_view, name='public_eposter_form'),  # Backward compatibility
    
    # Public Final Submission Forms (separate for E-Poster and Communication Orale)
    path('contributions/final-submission/eposter/<uuid:event_id>/', eposter_final_submission_form, name='public_final_submission_eposter'),
    path('contributions/final-submission/communication/<uuid:event_id>/', communication_orale_final_submission_form, name='public_final_submission_communication'),

    # Public E-Poster Gallery (final submitted PDFs, searchable by title/author)
    path('contributions/gallery/<uuid:event_id>/', eposter_public_gallery, name='public_eposter_gallery'),

    # ePoster API
    path('api/eposter/', include('dashboard.urls_eposter')),
    
    # Caisse (Cash Register)
    path('caisse/', include('caisse.urls')),
    
    # Browsable API auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)