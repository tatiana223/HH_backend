from app.permissions import *
from app.serializers import *
from rest_framework.decorators import authentication_classes
from .minio import add_pic
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from app.models import Vacancies, Responses, ResponsesVacancies
from .serializers import VacanciesSerializer
from .permissions import IsAuthenticatedOrReadOnly
from django.contrib.auth.models import User, AnonymousUser
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
import redis
from django.conf import settings
import uuid
from rest_framework.authentication import SessionAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import pickle
from django.utils.timezone import now
from django.http import JsonResponse
from app.services.qr_generate import generate_response_qr  # Если в utils.py


def get_user_from_session(request):
    session_id = request.COOKIES.get('session_id')

    if session_id:
        # Проверяем наличие session_id в Redis
        username = session_storage.get(session_id)
        if username:
            username = username.decode('utf-8')  # Декодируем bytes в строку
            try:
                user = User.objects.get(username=username)
                return user
            except User.DoesNotExist:
                return None
    return None

def GetDraftResponse(user):
    # Фильтруем отклики по пользователю и статусу, возвращаем первый результат
    return Responses.objects.filter(creator=user.id, status=1).first()

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Отключаем CSRF-проверку


#ДОМЕН УСЛУГИ
# GET список с фильтрацией. В списке услуг возвращается id заявки-черновика этого пользователя для страницы заявки и количество услуг в этой заявке
@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'vacancy_name',
            openapi.IN_QUERY,
            description='Название вакансии для фильтрации',
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "vacancies": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "vacancy_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "vacancy_name": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                            "description": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                            "money_from": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                            "money_to": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                            "city": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                            "name_company": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                            "peculiarities": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                            "url": openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                    nullable=False,
                ),
                "draft_responses": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    nullable=True,
                ),
                "quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    nullable=True,
                ),
            },
        )
    },
)
@api_view(['GET'])
def VacanciesList(request):
    def get_user_from_session(request):
        session_id = request.COOKIES.get('session_id')

        if session_id:
            # Проверяем наличие session_id в Redis
            username = session_storage.get(session_id)
            if username:
                username = username.decode('utf-8')  # Декодируем bytes в строку
                try:
                    user = User.objects.get(username=username)
                    return user
                except User.DoesNotExist:
                    return None
        return None

    vacancy_name = request.GET.get('vacancy_name', '')
    vacancies = Vacancies.objects.filter(status=1, vacancy_name__istartswith=vacancy_name)

    if not vacancies.exists():
        return JsonResponse({'error': 'No vacancies found'}, status=404)

    serializer = VacanciesSerializer(vacancies, many=True)

    # Извлечение пользователя из сессии
    user = get_user_from_session(request)

    draft_responses = None
    quantity = 0  # Устанавливаем начальное количество вакансий в черновике

    if user:
        try:
            draft_responses = Responses.objects.filter(status=1, creator=user).first()
            if draft_responses:
                # Считаем количество вакансий в отклике
                quantity = draft_responses.vacancies.count()
        except Responses.DoesNotExist:
            draft_responses = None

    response = {
        'vacancies': serializer.data,
        'draft_responses': draft_responses.pk if draft_responses else None,  # Идентификатор черновика
        'quantity': quantity,  # Количество вакансий в черновике отклика
    }

    return Response(response, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "vacancy_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                "vacancy_name": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                "description": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                "money_from": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                "money_to": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                "city": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                "name_company": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                "peculiarities": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                "url": openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticatedOrReadOnly])
def GetVacancyById(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id, status=1)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    serializer = VacanciesSerializer(vacancy, many=False)

    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(method='post', request_body=VacanciesSerializer)
@api_view(["POST"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAdmin])
def CreateVacancy(request):
    try:
        vacancy_data = request.data.copy()
        vacancy_data.pop('url', None)  # Исключаем поле 'image', если оно есть

        serializer = VacanciesSerializer(data=vacancy_data)
        serializer.is_valid(raise_exception=True)  # Проверка валидности данных
        new_vacancy = serializer.save()  # Сохраняем новую вакансию

        return Response(VacanciesSerializer(new_vacancy).data, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', request_body=VacanciesSerializer)
@api_view(["PUT"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAdmin])
def EditVacancy(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    vacancy_data = request.data.copy()
    vacancy_data.pop('url', None)  # Исключаем поле 'image', если оно не требуется для обновления

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
@permission_classes([IsAdmin])
@authentication_classes([CsrfExemptSessionAuthentication])
def DeleteVacancy(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"Ошибка": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Устанавливаем статус, чтобы "удалить" вакансию (например, 2 для удалённой)
    vacancy.status = 2  # Предполагается, что статус "2" означает удаление
    vacancy.save()

    # Возвращаем список активных вакансий (например, со статусом 1)
    vacancies = Vacancies.objects.filter(status=1)
    serializer = VacanciesSerializer(vacancies, many=True)
    return Response(serializer.data)

@swagger_auto_schema(method='post', responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "responses": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id_response": openapi.Schema(type=openapi.TYPE_INTEGER, description="Уникальный идентификатор заявки."),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER, description="Статус заявки."),
                        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Дата и время создания заявки."),
                        "creator": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя, создавшего заявку."),
                        "moderator": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Имя модератора заявки (если есть)."),
                        "submitted_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата сформирования заявки."),
                        "interview_date": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата интервью."),
                        "deleted_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата удаления заявки."),
                        "name_human": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="ФИО кондидата."),
                        "education": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Образование."),
                        "experience": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Опыт работы."),
                        "peculiarities_comm": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Особенности кондидата."),

                    },
                ),
                "vacancies": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "vacancy_id": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "vacancy_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "vacancy_name": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "money_from": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                                    "money_to": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                                    "city": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "name_company": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "peculiarities": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "url": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                            "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество записей для данной вакансии ."),
                        },
                    ),
                    description="Список вакансий, привязанных к заявке."
                ),
            },
        ),
    })

@api_view(["POST"])
def AddVacancyToDraft(request, vacancy_id):
    # Получаем пользователя из сессии
    user = get_user_from_session(request)

    if not user:
        return Response({"error": "Пользователь не авторизован"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"error": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    draft_response = GetDraftResponse(user)  # Получаем черновик заявки

    # Если черновика нет, создаем новый
    if draft_response is None:
        draft_response = Responses.objects.create(
            created_at=timezone.now(),  # Дата создания
            creator=user,  # Создатель заявки
            status=1,  # Статус "Действует"
        )

    # Проверка на существование вакансии в черновике
    existing_entry = ResponsesVacancies.objects.filter(request=draft_response, vacancy=vacancy).first()

    if existing_entry:
        # Увеличиваем количество каждый раз, даже если вакансия уже есть в заявке
        existing_entry.quantity += 1
        existing_entry.save()
    else:
        # Если вакансии нет в черновике, создаем новую запись
        try:
            new_entry = ResponsesVacancies.objects.create(
                request=draft_response,
                vacancy_id=vacancy_id,
                quantity=1  # Начинаем с 1
            )
            # Обновляем количество вакансий в черновике
            quantity = ResponsesVacancies.objects.filter(request=draft_response).count()
        except Exception as e:
            return Response({"error": f"Ошибка при создании связки: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Считываем количество вакансий в отклике после добавления новой вакансии
    quantity = ResponsesVacancies.objects.filter(request=draft_response).count()

    # Сериализация данных отклика
    response_serializer = ResponsesSerializer(draft_response, many=False)

    # Сериализация вакансий в отклике
    vacancies_responses = ResponsesVacancies.objects.filter(request=draft_response)
    vacancies_serializer = ResponsesVacanciesSerializer(vacancies_responses, many=True, fields=["vacancy_id", "quantity"])

    response_data = {
        'response': response_serializer.data,
        'vacancies': vacancies_serializer.data,
        'quantity': quantity  # Отправляем обновленное количество вакансий
    }

    # Возвращаем успешный ответ
    return Response(response_data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "image": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="binary",
                description="Новое изображение для вакансии."
            )
        },
        required=["image"],
    ),
    responses={
        status.HTTP_200_OK: VacanciesSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Изображение не предоставлено."),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Вакансия не найдена."),
            },
        ),
    }
)
@api_view(["POST"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAdmin])
def UpdateVacancyImage(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id)
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
@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "status",
            openapi.IN_QUERY,
            description="Статус заявки.",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        openapi.Parameter(
            "date_submitted_start",
            openapi.IN_QUERY,
            description="Начальная дата подачи заявки (в формате YYYY-MM-DDTHH:MM:SS).",
            type=openapi.TYPE_STRING,
            format="date-time",
            required=False,
        ),
        openapi.Parameter(
            "date_submitted_end",
            openapi.IN_QUERY,
            description="Конечная дата подачи заявки (в формате YYYY-MM-DDTHH:MM:SS).",
            type=openapi.TYPE_STRING,
            format="date-time",
            required=False,
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "id_response": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Уникальный идентификатор заявки."
                    ),
                    "status": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        description="Статус заявки: 1 - 'Черновик', 2 - 'Удалена', 3 - 'Сформирована', 4 - 'Завершена', 5 - 'Отклонена'.",
                    ),
                    "created_at": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format="date-time",
                        description="Дата и время создания заявки.",
                        nullable=False,
                    ),
                    "creator": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="Имя пользователя, который создал заявку.",
                        nullable=False,
                    ),
                    "moderator": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Имя модератора, обработавшего заявку (если есть)."
                    ),
                    "interview_date": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Дата интервью."
                    ),
                    "completed_at": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format="date-time",
                        nullable=True,
                        description="Дата и время завершения заявки (если была завершена)."
                    ),
                    "deleted_at": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format="date-time",
                        nullable=True,
                        description="Дата и время удаления заявки (если была удалена)."
                    ),
                    "name_human": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="ФИО кандидата."
                    ),
                    "education": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Образование."
                    ),
                    "experience": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Опыт работы."
                    ),
                    "peculiarities_comm": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Особенности кандидата."
                    ),

                },
            ),
        )
    },
)
@api_view(["GET"])
def ResponsesList(request):
    user = get_user_from_session(request)  # Получаем пользователя из сессии

    if not user:  # Если пользователь не найден, возвращаем ошибку
        return Response({"detail": "Authentication credentials were not provided."}, status=401)

    # Используем GetDraftResponse для получения чернового отклика
    draft_response = GetDraftResponse(user)
    if draft_response:
        print(f"Draft Response ID: {draft_response.id_response}")  # Пример использования

    status_filter = int(request.GET.get("status", 0))
    date_submitted_start = request.GET.get("date_submitted_start")
    date_submitted_end = request.GET.get("date_submitted_end")

    print(date_submitted_end)
    print(date_submitted_start)

    if user.is_staff or user.is_superuser:
        response = Responses.objects.all()
    else:
        response = Responses.objects.exclude(status__in=[1, 2])
        response = response.filter(creator=user)

    if status_filter:
        response = response.filter(status=status_filter)

    if date_submitted_start and parse_datetime(date_submitted_start):
        response = response.filter(created_at__gte=parse_datetime(date_submitted_start))

    if date_submitted_end and parse_datetime(date_submitted_end):
        response = response.filter(created_at__lt=parse_datetime(date_submitted_end))

    serializer = ResponsesSerializer(response, many=True)
    return Response(serializer.data)

# GET одна запись (поля заявки + ее услуги). При получении заявки возвращется список ее услуг с картинками
@swagger_auto_schema(
    method='get',
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "responses": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id_response": openapi.Schema(type=openapi.TYPE_INTEGER, description="Уникальный идентификатор заявки."),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER, description="Статус заявки."),
                        "created_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", description="Дата и время создания заявки."),
                        "creator": openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя, создавшего заявку."),
                        "moderator": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Имя модератора заявки (если есть)."),
                        "completed_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата завершения заявки."),
                        "deleted_at": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата удаления заявки."),
                        "name_human": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="ФИО кондидата."),
                        "education": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Образование."),
                        "experience": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Опыт работы."),
                        "peculiarities_comm": openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="Особенности кондидата."),
                        "interview_date": openapi.Schema(type=openapi.TYPE_STRING, format="date-time", nullable=True, description="Дата интервью."),
                    },
                ),
                "vacancies": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "vacancy_id": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "vacancy_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "vacancy_name": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "money_from": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                                    "money_to": openapi.Schema(type=openapi.TYPE_INTEGER, nullable=False),
                                    "city": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "name_company": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "peculiarities": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
                                    "url": openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                            "count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Количество записей для данноq вакансии."),
                        },
                    ),
                    description="Список вакансий, привязанных к заявке."
                ),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, description="Сообщение об ошибке.")
            },
        ),
    }
)
@api_view(["GET"])
def GetResponsesnById(request, id_response):
    user = get_user_from_session(request)  # Получаем пользователя из сессии

    if not user:  # Если пользователь не найден
        return Response({"Ошибка": "Пользователь не авторизован"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        if user.is_staff or user.is_superuser:  # Если пользователь администратор
            response = Responses.objects.get(id_response=id_response)
        else:  # Если пользователь обычный
            response = Responses.objects.get(id_response=id_response, creator=user, status=1)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание отклика не найдена"}, status=status.HTTP_404_NOT_FOUND)

    responses_serializer = ResponsesSerializer(response)

    vacancies_responses = ResponsesVacancies.objects.filter(request=response)
    vacancies_serializer = ResponsesVacanciesSerializer(vacancies_responses, many=True)

    response_data = {
        'responses': responses_serializer.data,
        'vacancies': vacancies_serializer.data
    }

    return Response(response_data, status=status.HTTP_200_OK)

# PUT изменения полей заявки по теме
@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name_human': openapi.Schema(type=openapi.TYPE_STRING, example="Якимова Татьяна Сергеевна"),
            'education': openapi.Schema(type=openapi.TYPE_STRING, example="МГТУ им.Баумана, бакалавриат"),
            'experience': openapi.Schema(type=openapi.TYPE_STRING, example="3 года опыта работы с Java"),
            'peculiarities_comm': openapi.Schema(type=openapi.TYPE_STRING, example="Нарушение слуха"),
        }
    ),
    responses={
        status.HTTP_200_OK: ResponsesSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Нет данных для обновления или поля не разрешены."),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Заявка на создание вакансии не найдена."),
            },
        ),
    }
)
@api_view(["PUT"])
#@authentication_classes([CsrfExemptSessionAuthentication])
#@permission_classes([IsAuthenticated])
def UpdateResponses(request, id_response):
    user = get_user_from_session(request)

    if not user:
        return Response({"Ошибка": "Пользователь не авторизован"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    allowed_fields = ['name_human', 'education', 'experience', 'peculiarities_comm']

    data = {key: value for key, value in request.data.items() if key in allowed_fields}

    if not data:
        return Response({"Ошибка": "Нет данных для обновления или поля не разрешены"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResponsesSerializer(responses, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT сформировать создателем (дата формирования). Происходит проверка на обязательные поля
@swagger_auto_schema(
    method='put',
    responses={
        status.HTTP_200_OK: ResponsesSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Не заполнены данные об отклике."),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Заявка на создание отклика не найдена."),
            },
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Заявку нельзя изменить, так как она не в статусе 'Черновик'."),
            },
        ),
    }
)
@api_view(["PUT"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def UpdateStatusUser(request, id_response):

    try:
        if request.user.is_staff or request.user.is_superuser:
            response = Responses.objects.get(id_response=id_response)
        else:
            response = Responses.objects.get(id_response=id_response, creator=request.user, status=1)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if response.status != 1:
        return Response({"Ошибка": "Заявку нельзя изменить, так как она не в статусе 'Черновик'"}, status=status.HTTP_400_BAD_REQUEST)

    required_fields = ['name_human', 'education', 'experience', 'peculiarities_comm']
    missing_fields = [field for field in required_fields if not getattr(response, field)]

    if missing_fields:
        return Response(
            {"Ошибка": f"Не заполнены обязательные поля: {', '.join(missing_fields)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Use request.data instead of request.body
    response.status = 3
    response.submitted = timezone.now()
    response.save()

    serializer = ResponsesSerializer(response, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Новый статус заявки (4 - Завершена, 5 - Отклонена)",
                example=4
            ),
        },
        required=['status']
    ),
    responses={
        status.HTTP_200_OK: ResponsesSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Неверные данные или обязательные поля не заполнены."),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Заявка на создание отклика не найдена."),
            },
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Заявка ещё не сформирована или статус не разрешён."),
            },
        ),
    }
)
@api_view(["PUT"])
def UpdateStatusAdmin(request, id_response):
    # Получаем пользователя из сессии
    user = get_user_from_session(request)
    if not user:
        return JsonResponse({"Ошибка": "Вы не авторизованы"}, status=401)

    # Проверяем, является ли пользователь суперпользователем
    if not user.is_superuser:
        return JsonResponse(
            {"Ошибка": "У вас нет прав на выполнение этого действия"},
            status=403
        )

    # Получаем отклик
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return JsonResponse({"Ошибка": "Заявка на создание вакансии не найдена"}, status=404)

    # Проверяем, является ли пользователь создателем отклика
    if responses.creator == user:
        return JsonResponse({"Ошибка": "Вы не можете изменить статус своей заявки"}, status=403)

    # Проверяем корректность статуса
    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if responses.creator == request.user:
        return Response({"Ошибка": "Вы не можете изменить статус этой заявки"}, status=status.HTTP_403_FORBIDDEN)
    request_status = int(request.data["status"])

    if request_status not in [4, 5]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if responses.status != 3:
        return Response({"Ошибка": "Заявка ещё не сформирована"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    responses.completed_at = timezone.now()
    responses.status = request_status
    responses.moderator = request.user
    responses.duration_days = (responses.completed_at - responses.created_at).days

    #Qr-code
    if responses.status == 4:
        qr_code = generate_response_qr(responses)
        if not qr_code:
            print("Ошибка: QR-код не сгенерировался!")
        responses.qr = qr_code

        updated_data = request.data.copy()
        updated_data["qr"] = qr_code

    responses.save()
    serializer = ResponsesSerializer(responses, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def DeleteResponses(request, id_response):
    def get_user_from_session(request):
        session_id = request.COOKIES.get('session_id')

        if session_id:
            # Проверяем наличие session_id в Redis
            username = session_storage.get(session_id)
            if username:
                username = username.decode('utf-8')  # Декодируем bytes в строку
                try:
                    user = User.objects.get(username=username)
                    return user
                except User.DoesNotExist:
                    return None
        return None

    # Извлекаем пользователя из сессии
    user = get_user_from_session(request)

    if not user:
        return Response({"Ошибка": "Пользователь не авторизован"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        responses = Responses.objects.get(id_response=id_response)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание вакансии не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Проверяем, что пользователь является создателем заявки
    if responses.creator != user:
        return Response({"Ошибка": "Нет прав на удаление данной заявки"}, status=status.HTTP_403_FORBIDDEN)

    # Устанавливаем статус на "Удалена"
    responses.status = 2
    responses.save()

    serializer = ResponsesSerializer(responses, many=False)

    return Response(serializer.data, status=status.HTTP_200_OK)


# Домен м-м
# DELETE удаление из заявки (без PK м-м)
@api_view(["DELETE"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def DeleteVacancyFromonResponse(request, id_response, vacancy_id):
    try:
        vacancy_response = ResponsesVacancies.objects.get(request=id_response, vacancy=vacancy_id)
    except ResponsesVacancies.DoesNotExist:
        return Response({"Ошибка": "Связь между заявкой и вакансией не найдена"}, status=status.HTTP_404_NOT_FOUND)

    response = Responses.objects.get(id_response=id_response)

    if not (request.user.is_staff or request.user.is_superuser):
        if response.creator != request.user or response.status != 1:
            return Response({"detail": "Вы не имеете права выполнять это действие."}, status=status.HTTP_403_FORBIDDEN)

    vacancy_response.delete()

    return Response({"detail": "Связь успешно удалена"}, status=status.HTTP_200_OK)

# PUT изменение количества/порядка/значения в м-м (без PK м-м)
@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'quantity': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Количество откликов для данной вакансии в заявке.",
                example=1
            ),
        },
        required=['quantity']
    ),
    responses={
        status.HTTP_200_OK: ResponsesVacanciesSerializer,
        status.HTTP_400_BAD_REQUEST: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Количество не предоставлено"),
            },
        ),
        status.HTTP_403_FORBIDDEN: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "detail": openapi.Schema(type=openapi.TYPE_STRING, example="You do not have permission to perform this action."),
            },
        ),
        status.HTTP_404_NOT_FOUND: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "Ошибка": openapi.Schema(type=openapi.TYPE_STRING, example="Связь между вакансией откликом не найдена"),
            },
        ),
    }
)
@api_view(["PUT"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def UpdateResponsesVacancies(request, id_response, vacancy_id):
    try:
        vacancy_response = ResponsesVacancies.objects.get(request=id_response, vacancy=vacancy_id)
    except ResponsesVacancies.DoesNotExist:
        return Response({"Ошибка": "Связь между вакансией и заявкой не найдена"}, status=status.HTTP_404_NOT_FOUND)

    response = Responses.objects.get(id_response=id_response)

    if request.user.is_staff == False or request.user.is_superuser == False:
        if response.creator != request.user or response.status != 1:
            return Response({"detail": "You do not have permission to perform this action."},
                            status=status.HTTP_403_FORBIDDEN)

    quantity = request.data.get("quantity")  # Используем правильное имя поля

    if quantity is not None:
        vacancy_response.quantity = quantity  # Обновляем поле quantity
        vacancy_response.save()
        serializer = ResponsesVacanciesSerializer(vacancy_response, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Количество не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)


# Домен пользователь
# PUT пользователя (личный кабинет)
@swagger_auto_schema(method='put', request_body=UserSerializer)
@api_view(["PUT"])
#@authentication_classes([CsrfExemptSessionAuthentication])
#@permission_classes([IsAuthenticated])
def UpdateUser(request, user_id):
    # Получаем текущего пользователя из сессии
    current_user = get_user_from_session(request)
    if not current_user:
        return Response({"detail": "Пользователь не найден в сессии."}, status=status.HTTP_404_NOT_FOUND)

    # Проверяем, существует ли пользователь с данным user_id
    if not User.objects.filter(id=user_id).exists():
        return Response({"detail": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(id=user_id)

    # Проверяем права доступа
    if not request.user.is_superuser and user != current_user:
        return Response({"detail": "У вас нет прав для выполнения этого действия."}, status=status.HTTP_403_FORBIDDEN)

    # Проверяем черновик отклика
    draft_response = GetDraftResponse(current_user)
    if draft_response:
        return Response({"detail": "Черновик отклика существует, обновление запрещено."}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data
    if 'password' in data:
        # Хэшируем пароль перед сохранением
        user.set_password(data['password'])
        data.pop('password', None)

    # Создаем сериализатор с partial=True для частичного обновления
    serializer = UserSerializer(user, data=data, partial=True)

    # Проверяем валидность данных
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Сохраняем обновленные данные
    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model_class = User

    http_method_names = ['create', 'list', 'get', 'post', 'delete']

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsManager | IsAdmin]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя (только username и password)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Имя пользователя'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя', minLength=8),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Response('Успешная регистрация'),
            400: openapi.Response('Ошибка регистрации, например, если пользователь с таким username уже существует'),
        }
    )
    @authentication_classes([CsrfExemptSessionAuthentication])
    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(username=serializer.data['username'],
                                     password=serializer.data['password'],
                                     is_superuser=serializer.data['is_superuser'],
                                     is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




#@csrf_exempt
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description="Имя пользователя"),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description="Пароль пользователя"),
        },
        required=['username', 'password']
    ),
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Успешная аутентификация",
            schema=UserSerializer
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Ошибка аутентификации, неверные данные",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                    "error": openapi.Schema(type=openapi.TYPE_STRING, example="Неверное имя пользователя или пароль."),
                },
            ),
        ),
        status.HTTP_409_CONFLICT: openapi.Response(
            description="Ошибка в данных пользователя",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                    "error": openapi.Schema(type=openapi.TYPE_STRING, example="Ошибка в данных пользователя."),
                },
            ),
        ),
    }
)


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)

    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        serializer = UserSerializer(user, data=request.data, many=False, partial=True)

        if not serializer.is_valid():
            return Response(
                {"success": False, "error": "Ошибка в данных пользователя."},
                status=status.HTTP_409_CONFLICT
            )

        user_data = serializer.data
        response = Response(user_data, status=status.HTTP_200_OK)
        response.set_cookie('session_id', random_key,secure=True, samesite='none')
        return response
    else:
        return Response(
            {"success": False, "error": "Неверное имя пользователя или пароль."},
            status=status.HTTP_400_BAD_REQUEST
        )


def delete_cookie(self, key: str, path: str = "/", domain: str = None) -> None:
    self.set_cookie(key, expires=0, max_age=0, path=path, domain=domain)

#@csrf_exempt
@api_view(["POST"])
#@permission_classes([AllowAny])
#@authentication_classes([])

def logout_view(request):
    session_id = request.COOKIES.get('session_id')
    if session_id:
        session_storage.delete(session_id)
        response = Response({"message": "Вы вышли из аккаунта."}, status=status.HTTP_200_OK)
        response.delete_cookie("session_id")
        return response
    return Response({"error": "Необходима аутентификация."}, status=status.HTTP_401_UNAUTHORIZED)


# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)