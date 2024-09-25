from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('companies/<int:company_id>/', company),
    path('vacancies/<int:vacancy_id>/', vacancy),
]