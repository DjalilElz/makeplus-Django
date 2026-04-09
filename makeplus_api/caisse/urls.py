"""
URL Configuration for Caisse (Cash Register)
"""

from django.urls import path
from . import views

app_name = 'caisse'

urlpatterns = [
    # Authentication
    path('login/', views.caisse_login, name='login'),
    path('logout/', views.caisse_logout, name='logout'),
    
    # Dashboard
    path('', views.caisse_dashboard, name='dashboard'),
    
    # Participant Search
    path('search/', views.search_participant, name='search_participant'),
    path('participant-paid-items/<int:participant_id>/', views.get_participant_paid_items, name='participant_paid_items'),
    
    # Transaction Processing
    path('process-transaction/', views.process_transaction, name='process_transaction'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transactions/<int:transaction_id>/cancel/', views.cancel_transaction, name='cancel_transaction'),
    
    # Badge Printing
    path('print-badge/<int:participant_id>/', views.print_badge, name='print_badge'),
]
