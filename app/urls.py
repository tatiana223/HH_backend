from django.urls import include, path
from app import views
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    path('vacancies/', views.VacanciesList, name='vacancies_list'),
    path('vacancies/<int:vacancy_id>/', views.GetVacancyById, name='get_vacancy_by_id'),
    path('vacancies/create_vacancy/', views.CreateVacancy, name='create_vacancy'),
    path('vacancies/<int:vacancy_id>/edit_vacancy/', views.EditVacancy, name='edit_vacancy'),
    path('vacancies/<int:vacancy_id>/delete_vacancy/', views.DeleteVacancy, name='delete_vacancy'),
    path('vacancies/<int:vacancy_id>/add_to_response/', views.AddVacancyToDraft, name='add_vacancy_to_response'),
    path('vacancies/<int:vacancy_id>/update_image/', views.UpdateVacancyImage, name='update_vacancy_image'),

    path('responses/', views.ResponsesList, name='responses_list'),
    path('responses/<int:id_response>/', views.GetResponsesnById, name='get_responses_by_id'),
    path('responses/<int:id_response>/update_vacancy/', views.UpdateResponses, name='update_responses'),
    path('responses/<int:id_response>/update_status_user/', views.UpdateStatusUser, name='update_status_user'),
    path('responses/<int:id_response>/update_status_admin/', views.UpdateStatusAdmin, name='update_status_admin'),
    path('responses/<int:id_response>/delete_response/', views.DeleteResponses, name='delete_response'),

    path('vacancies_responses/<int:mm_id>/delete_vacancy_from_response/', views.DeletVacancyFromonResponse, name='delete_vacancy_from_response'),
    path('vacancies_responses/<int:mm_id>/update_response/', views.UpdateResponsesVacancies, name='update_responses'),

    path('users/register/', views.register, name='register'),
    path('users/<int:user_id>/update_user/', views.UpdateUser, name='update_user'),
    path('users/login/', views.login, name='login'),
    path('users/logout/', views.logout_view, name='logout'),
]