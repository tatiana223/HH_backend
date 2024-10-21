from django.contrib.auth import authenticate, logout
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from app.serializers import *
from rest_framework import status
from .minio import add_pic
from app.models import Vacancies, Responses, ResponsesVacancies

def GetCurrentUser():
    return User.objects.filter(is_superuser=False).first()


def GetModerator():
    return User.objects.filter(is_superuser=True).first()


def GetDraftResponse():
    current_user = GetCurrentUser()
    return Responses.objects.filter(creator=current_user.id, status=1).first()


@api_view(["GET"])
def VacanciesList(request):
    vacancy_name = request.GET.get("vacancy_name", '')
    vacancies = Vacancies.objects.filter(name__istartswith=vacancy_name)

    serializer = VacanciesSerializer(vacancies, many=True)

    # Предполагается, что у вас есть функция для получения черновика заявки
    if GetDraftResponse():
        id_response = GetDraftResponse().id_response
        count = ResponsesVacancies.objects.filter(request__id_response__id=id_response).count()
    else:
        id_response = None
        count = 0

    response = {
        "vacancies": serializer.data,
        "draft_response": id_response,
        "count": count,
    }
    return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def GetVacancyById(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(id_vacancies=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    serializer = VacanciesSerializer(vacancy, many=False)

    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def CreateVacancy(request):
    vacancy_data = request.data.copy()
    vacancy_data.pop('image', None)  # Опционально, если вы хотите исключить поле 'image'

    serializer = VacanciesSerializer(data=vacancy_data)
    serializer.is_valid(raise_exception=True)  # Проверка валидности с автоматической обработкой ошибок
    new_vacancy = serializer.save()  # Сохраняем новую вакансию
    # Возвращаем данные с новой вакансией
    return Response(VacanciesSerializer(new_vacancy).data, status=status.HTTP_201_CREATED)

@api_view(["PUT"])
def EditVacancy(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(id_vacancies=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    vacancy_data = request.data.copy()
    vacancy_data.pop('image', None)  # Исключаем поле 'image', если оно не требуется для обновления

    # Частичное обновление вакансии
    serializer = VacanciesSerializer(vacancy, data=vacancy_data, partial=True)
    serializer.is_valid(raise_exception=True)
    edited_vacancy = serializer.save()

    # Обработка изменения изображения, если оно предоставлено
    pic = request.FILES.get("image")
    if pic:
        pic_result = add_pic(edited_vacancy, pic)
        if 'error' in pic_result.data:
            return pic_result  # Возвращаем ошибку, если загрузка изображения не удалась

    # Возвращаем обновлённые данные вакансии
    return Response(VacanciesSerializer(edited_vacancy).data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def DeleteVacancy(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(id_vacancies=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Устанавливаем статус, чтобы "удалить" вакансию (например, 2 для удалённой)
    vacancy.status = 2  # Предполагается, что статус "2" означает удаление
    vacancy.save()

    # Возвращаем список активных вакансий (например, со статусом 1)
    vacancies = Vacancies.objects.filter(status=1)
    serializer = VacanciesSerializer(vacancies, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def AddVacancyToDraft(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(id_vacancies=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"error": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    draft_response = GetDraftResponse()  # Предполагается, что у вас есть функция для получения черновика заявки

    # Если черновика нет, создаем новый
    if draft_response is None:
        draft_response = Responses.objects.create(
            created_at=timezone.now(),  # Дата создания
            creator=GetCurrentUser(),  # Создатель заявки (через пользовательскую функцию)
            status=1,  # Статус "Действует"
        )

    # Проверка, есть ли уже эта вакансия в черновике
    existing_entry = ResponsesVacancies.objects.filter(request=draft_response, vacancy=vacancy).first()

    if existing_entry:
        # Увеличиваем количество, если вакансия уже есть в заявке
        existing_entry.quantity += 1
        existing_entry.save()
    else:
        # Если вакансии нет в черновике, создаем новую запись
        try:
            ResponsesVacancies.objects.create(
                request=draft_response,
                vacancy=vacancy,
                quantity=1  # Начинаем с 1
            )
        except Exception as e:
            return Response({"error": f"Ошибка при создании связки: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Сериализация и возврат обновлённого черновика
    serializer = ResponsesSerializer(draft_response)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
def UpdateVacancyImage(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(id_vacancies=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"error": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    image = request.FILES.get("image")

    if image is not None:
        # Здесь заменяем старое изображение на новое, используя функцию add_pic
        pic_result = add_pic(vacancy, image)  # Вы используете MinIO или другую систему для хранения изображений
        if 'error' in pic_result.data:
            return pic_result  # Если произошла ошибка, возвращаем её


        # Сериализация и возврат обновлённой вакансии
        serializer = VacanciesSerializer(vacancy)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"error": "Изображение не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)



#ДОМЕН ЗАЯВКИ
#GET список (кроме удаленных и черновика, поля модератора и создателя через логины) с фильтрацией по диапазону даты формирования и статусу
@api_view(["GET"])
def ResponsesList(request):
    status = int(request.GET.get("status", 0))
    date_submitted_start = request.GET.get("date_submitted_start")
    date_submitted_end = request.GET.get("date_submitted_end")

    #responses = Responses.objects.exclude(status__in=[1, 2])
    responses = Responses.objects.all()
    if status:
        responses = responses.filter(status=status)

    if date_submitted_start and parse_datetime(date_submitted_start):
        responses = responses.filter(submitted__gte=parse_datetime(date_submitted_start))

    if date_submitted_end and parse_datetime(date_submitted_end):
        responses = responses.filter(submitted__lt=parse_datetime(date_submitted_end))

    serializer = ResponsesSerializer(responses, many=True)

    return Response(serializer.data)

# GET одна запись (поля заявки + ее услуги). При получении заявки возвращется список ее услуг с картинками
@api_view(["GET"])
def GetResponsesnById(request, id_response):
    try:
        # Используйте id_response напрямую, так как это первичный ключ
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    responses_serializer = ResponsesSerializer(responses)

    # Здесь вы можете фильтровать ResponsesVacancies по id_response, если это правильно
    vacancies_responses = ResponsesVacancies.objects.filter(request =responses)  # Исправьте здесь, если 'response' - это правильное имя поля
    vacancies_serializer = ResponsesVacanciesSerializer(vacancies_responses, many=True)

    response_data = {
        'responses': responses_serializer.data,
        'vacancies': vacancies_serializer.data
    }

    return Response(response_data, status=status.HTTP_200_OK)

# PUT изменения полей заявки по теме
@api_view(["PUT"])
def UpdateResponses(request, id_response):
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    allowed_fields = ['name_human']

    data = {key: value for key, value in request.data.items() if key in allowed_fields}

    if not data:
        return Response({"Ошибка": "Нет данных для обновления или поля не разрешены"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResponsesSerializer(responses, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT сформировать создателем (дата формирования). Происходит проверка на обязательные поля
@api_view(["PUT"])
def UpdateStatusUser(request, id_response):
    if request.method != 'PUT':
        return Response({"error": "Метод не разрешён"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    '''if responses.status != 1:
        return Response({"Ошибка": "Заявку нельзя изменить, так как она не в статусе 'Черновик'"}, status=status.HTTP_400_BAD_REQUEST)
'''
    required_fields = ['name_human']

    missing_fields = [field for field in required_fields if not getattr(responses, field)]

    if missing_fields:
        return Response(
            {"Ошибка": f"Не заполнены обязательные поля: {', '.join(missing_fields)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    responses.status = 3
    responses.submitted = timezone.now()
    responses.save()

    serializer = ResponsesSerializer(responses, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["PUT"])
def UpdateStatusAdmin(request, id_response):
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [4, 5]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if responses.status != 3:
        return Response({"Ошибка": "Заявка ещё не сформирована"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    responses.completed_at = timezone.now()
    responses.status = request_status
    responses.moderator = GetModerator()
    responses.save()

    serializer = ResponsesSerializer(responses, many=False)

    return Response(serializer.data)

# DELETE удаление (дата формирования)
@api_view(["DELETE"])
def DeleteResponses(request, id_response):
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    '''if responses.status == 1:
        return Response({"Ошибка": "Нельзя удалить заявку со статусом 'Черновик'"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
'''
    # Установите статус на "Удалена"
    responses.status = 2
    responses.save()

    return Response(status=status.HTTP_204_NO_CONTENT)  # Возврат 204 при успешном удалении

# Домен м-м
# DELETE удаление из заявки (без PK м-м)
@api_view(["DELETE"])
def DeletVacancyFromonResponse(request, mm_id):
    try:
        vacancy_response = ResponsesVacancies.objects.get(mm_id=mm_id)
    except ResponsesVacancies.DoesNotExist:
        return Response({"Ошибка": "Связь между городом и заявкой не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Сохраняем ID заявки перед удалением связи
    id_response = vacancy_response.request.id_response

    # Удаляем связь
    vacancy_response.delete()

    # Обновляем данные заявки
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена после удаления города"}, status=status.HTTP_404_NOT_FOUND)

    # Сериализуем обновлённую отправку
    serializer = ResponsesSerializer(responses, many=False)

    # Возвращаем обновлённые данные отправки
    return Response(serializer.data, status=status.HTTP_200_OK)

# PUT изменение количества/порядка/значения в м-м (без PK м-м)
@api_view(["PUT"])
def UpdateResponsesVacancies(request, mm_id):
    try:
        vacancy_response = ResponsesVacancies.objects.get(mm_id=mm_id)
    except ResponsesVacancies.DoesNotExist:
        return Response({"Ошибка": "Связь между вакансией и заявкой не найдена"}, status=status.HTTP_404_NOT_FOUND)

    quantity = request.data.get("quantity")  # Используем правильное имя поля

    if quantity is not None:
        vacancy_response.quantity = quantity  # Обновляем поле quantity
        vacancy_response.save()
        serializer = ResponsesVacanciesSerializer(vacancy_response, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Количество не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)

# Домен пользователь
# POST регистрация
@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    # Проверка валидности данных
    if not serializer.is_valid():
        return Response({"Ошибка": "Некорректные данные"}, status=status.HTTP_400_BAD_REQUEST)

    # Сохранение нового пользователя
    user = serializer.save()

    # Сериализация и возврат данных нового пользователя
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# PUT пользователя (личный кабинет)
@api_view(["PUT"])
def UpdateUser(request, user_id):
    if not User.objects.filter(id=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(id=user_id)
    serializer = UserSerializer(user, data=request.data, many=False, partial=True)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data)

# POST аутентификация
@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    return Response(status=status.HTTP_200_OK)

# POST деавторизация
@api_view(["POST"])
def logout_view(request):
    # request.user.auth_token.delete()
    logout(request)

    return Response(status=status.HTTP_200_OK)

