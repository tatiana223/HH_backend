from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone

from django.http import HttpResponseRedirect
from django.urls import reverse

from django.db import connection
from app.models import Vacancies, Request, RequestServices

def GetDraftResponse():
    current_user = GetCurrentUser()
    return Request.objects.filter(creator=current_user.id, status=1).first()  # так как у пользователя только один черновик, то берем первый элемент, иначе None

def GetCurrentUser():
    return User.objects.filter(is_superuser=False).first()

def GetAppVacanciesCount(id):
    return RequestServices.objects.filter(request=id).count()
def index(request):
    name_vacancy = request.GET.get("name_vacancy", "");
    vacancies = Vacancies.objects.filter(name__istartswith=name_vacancy);
    context = {
        "vacancies": vacancies,
        "name_vacancy": name_vacancy
    }
    draft_response = GetDraftResponse()
    if draft_response:
        context["vacancies_count"] = GetAppVacanciesCount(draft_response.id)
        context["draft_response"] = draft_response
    else:
        context["draft_response"] = None
        context["vacancies_count"] = 0  # Например, можно установить 0, если черновик отсутствует

    return render(request, "home_page.html", context)

def vacancy(request, vacancy_id):
    vacancy = get_object_or_404(Vacancies, id=vacancy_id)
    context = {
        "vacancy": vacancy
    }
    return render(request, "vacancy_page.html", context)

def response(request, id):
    request_services = RequestServices.objects.filter(request=id)
    vacancies_ids = request_services.values_list('vacancy', flat=True)
    vacancies = Vacancies.objects.filter(id__in=vacancies_ids)

    context = {
        "vacancies": vacancies,
        "request": get_object_or_404(Request, id=id, status=1),
    }

    return render(request, "responses.html", context)

def add_vacancy(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        draft_response = GetDraftResponse()

        # если черновика нет, создаем новый
        if draft_response is None:
            draft_response = Request.objects.create(
                status = 1,
                created_at = timezone.now(),
                creator = GetCurrentUser(),
                formed_at = timezone.now(),
            )

        # есть ли уже этот город в черновике
        existing_entry = RequestServices.objects.filter(request=draft_response, vacancy=id).first()

        if not existing_entry:
            # увеличиваем, если город уже есть в заявке

            # если города нет в заявке, создаем новую запись
            RequestServices.objects.create(
                request=draft_response,
                vacancy=Vacancies.objects.get(id=id),
            )
        return HttpResponseRedirect(reverse('home_page'))
    return HttpResponseRedirect(reverse('home_page'))

def delete_response(request):
    if request.method == 'POST':
        request_id = request.POST.get('id')  # Переименовали переменную

        # проверяем, существует ли заявка с таким ID
        draft_request = Request.objects.filter(id=request_id).first()
        if draft_request:
            # выполняем SQL-запрос для изменения статуса заявки на "Удалена"
            with connection.cursor() as cursor:
                cursor.execute("UPDATE requests SET status = 2 WHERE id = %s", [request_id])

        return HttpResponseRedirect(reverse('home_page'))
