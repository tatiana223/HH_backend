from django.urls import path
from app.views import index, vacancy, response, add_vacancy, delete_response

urlpatterns = [
    path('', index, name='home_page'),
    path('vacancies/<int:vacancy_id>/', vacancy, name='vacancy'),
    path('responses/<int:id>/', response, name='response'),
    path('add_vacancy/', add_vacancy, name='add_vacancy'),
    path('delete_response/', delete_response, name='delete_response'),
]
