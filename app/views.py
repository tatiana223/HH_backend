from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse

from django.db import connection
from app.models import Vacancies, Responses, ResponsesVacancies

def GetDraftResponse():
    current_user = GetCurrentUser()
    if current_user is None:  # Проверка на наличие текущего пользователя
        return None
    return Responses.objects.filter(creator=current_user, status=1).first()

def GetCurrentUser():
    return User.objects.filter(is_superuser=False).first()

def GetAppVacanciesCount(id_response):
    return ResponsesVacancies.objects.filter(request=id_response).count()

def index(request):
    name_vacancy = request.GET.get("name_vacancy", "")
    vacancies = Vacancies.objects.filter(name__istartswith=name_vacancy)
    context = {
        "vacancies": vacancies,
        "name_vacancy": name_vacancy
    }
    draft_response = GetDraftResponse()
    if draft_response:
        context["vacancies_count"] = GetAppVacanciesCount(draft_response.id_response)
        context["draft_response"] = draft_response
    else:
        context["draft_response"] = None
        context["vacancies_count"] = 0  # Устанавливаем 0, если черновик отсутствует

    return render(request, "home_page.html", context)

def vacancy(request, vacancy_id):
    vacancy = get_object_or_404(Vacancies, id_vacancies=vacancy_id)
    context = {
        "vacancy": vacancy
    }
    return render(request, "vacancy_page.html", context)

from django.shortcuts import render, get_object_or_404, redirect
from .models import Responses, ResponsesVacancies, Vacancies

def response(request, id):
    request_obj = Responses.objects.filter(id_response=id, status=1).first()

    if not request_obj:
        # Вместо raise Http404, рендерим страницу с сообщением
        return render(request, 'no_response.html', {"message": "Отклик с таким ID не найден."})

    request_services = ResponsesVacancies.objects.filter(request=request_obj)
    vacancies_ids = request_services.values_list('vacancy__id_vacancies', flat=True)
    vacancies = Vacancies.objects.filter(id_vacancies__in=vacancies_ids)

    context = {
        "vacancies": vacancies,
        "response": request_obj,  # Изменили на 'response'
    }

    return render(request, "responses.html", context)


def add_vacancy(request):
    if request.method == 'POST':
        id_vacancies = request.POST.get('id_vacancies')
        draft_response = GetDraftResponse()

        if draft_response is None:
            draft_response = Responses.objects.create(
                status=1,
                created_at=timezone.now(),
                creator=GetCurrentUser(),
                formed_at=timezone.now(),
            )

        existing_entry = ResponsesVacancies.objects.filter(request=draft_response, vacancy=id_vacancies).first()

        if not existing_entry:
            try:
                vacancy = Vacancies.objects.get(id_vacancies=id_vacancies)
                ResponsesVacancies.objects.create(
                    request=draft_response,
                    vacancy=vacancy,
                )
            except ObjectDoesNotExist:
                print(f"Вакансия с ID {id_vacancies} не найдена.")

        return HttpResponseRedirect(reverse('home_page'))
    return HttpResponseRedirect(reverse('home_page'))


def delete_response(request):
    if request.method == 'POST':
        id_response = request.POST.get('id_response')

        draft_request = Responses.objects.filter(id_response=id_response).first()
        if draft_request:
            draft_request.status = 2  # Меняем статус на "Удалена"
            draft_request.save()  # Сохраняем изменения

        return HttpResponseRedirect(reverse('home_page'))
