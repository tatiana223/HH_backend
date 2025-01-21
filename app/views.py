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

def GetDraftResponse(request):
    if not request.user.is_authenticated:
        return None
    try:
        return Responses.objects.filter(creator=request.user, status=1).first()
    except Responses.DoesNotExist:
        return None


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
                "count": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    nullable=True,
                ),
            },
        )
    },
)
@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([AuthBySessionIDIfExists])
def VacanciesList(request):
    vacancy_name = request.GET.get('vacancy_name', '')

    vacancies = Vacancies.objects.filter(status=True).filter(vacancy_name__istartswith=vacancy_name)

    if not vacancies.exists():
        return JsonResponse({'error': 'No vacancies found'}, status=404)
    serializer = VacanciesSerializer(vacancies, many=True)

    draft_responses = None
    vacancies_to_response = None
    if request.user and request.user.is_authenticated:
        try:
            if request.user and request.user.is_authenticated:
                draft_responses = Responses.objects.filter(status=1, creator=request.user).first()
                vacancies_to_response = len(draft_responses.vacancies.all()) if draft_responses else None
            else:
                draft_responses = None
                vacancies_to_response = None
        except Responses.DoesNotExist:
            draft_responses = None

    response = {
        'vacancies': serializer.data,
        'draft_responses': draft_responses.pk if draft_responses else None,
        'vacancies_to_response': vacancies_to_response,
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
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAdmin])
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
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def AddVacancyToDraft(request, vacancy_id):
    try:
        vacancy = Vacancies.objects.get(vacancy_id=vacancy_id)
    except Vacancies.DoesNotExist:
        return Response({"error": "Вакансия не найдена"}, status=status.HTTP_404_NOT_FOUND)

    draft_response = GetDraftResponse(request)  # Получаем черновик заявки

    # Если черновика нет, создаем новый
    if draft_response is None:
        draft_response = Responses.objects.create(
            created_at=timezone.now(),  # Дата создания
            creator=request.user,  # Создатель заявки
            status=1,  # Статус "Действует"
        )

    # Проверка на существование вакансии в черновике
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
    response_serializer = ResponsesSerializer(draft_response, many=False)
    vacancies_responses = ResponsesVacancies.objects.filter(request=draft_response)
    vacancies_serializer = ResponsesVacanciesSerializer(vacancies_responses, many=True, fields=["vacancy", "quantity"])

    response_data = {
        'responses': response_serializer.data,
        'vacancies': vacancies_serializer.data
    }
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
                    "interview_date": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        nullable=True,
                        description="Дата интервью."
                    ),
                },
            ),
        )
    },
)
@api_view(["GET"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def ResponsesList(request):
    status_filter = int(request.GET.get("status", 0))
    date_submitted_start = request.GET.get("formed_at")
    date_submitted_end = request.GET.get("deleted_at")

    if request.user.is_staff or request.user.is_superuser:
        response = Responses.objects.all()
    else:
        response = Responses.objects.exclude(status__in=[1, 2])
        response = response.filter(creator=request.user)

    if status_filter :
        response = response.filter(status=status_filter)

    if date_submitted_start and parse_datetime(date_submitted_start):
        response = response.filter(submitted__gte=parse_datetime(date_submitted_start))

    if date_submitted_end and parse_datetime(date_submitted_end):
        response = response.filter(submitted__lt=parse_datetime(date_submitted_end))


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
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, nullable=False),
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
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def GetResponsesnById(request, id_response):
    try:
        if request.user.is_staff or request.user.is_superuser:
            response = Responses.objects.get(id_response=id_response)
        else:
            response = Responses.objects.get(id_response=id_response, creator=request.user, status=1)
    except Responses.DoesNotExist:
        return Response({"Ошибка": "Заявка на создание отклика не найдена"}, status=status.HTTP_404_NOT_FOUND)

    responses_serializer = ResponsesSerializer(response)


    vacancies_responses = ResponsesVacancies.objects.filter(request =response)
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
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def UpdateResponses(request, id_response):
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
    if request.method != 'PUT':
        return Response({"error": "Метод не разрешён"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsManager | IsAdmin])
def UpdateStatusAdmin(request, id_response):
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

    responses.save()

    serializer = ResponsesSerializer(responses, many=False)

    return Response(serializer.data)

# DELETE удаление (дата формирования)
@api_view(["DELETE"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsManager | IsAdmin])
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
    responses.deleted_at = timezone.now()
    responses.save()

    return Response(status=status.HTTP_204_NO_CONTENT)  # Возврат 204 при успешном удалении

# Домен м-м
# DELETE удаление из заявки (без PK м-м)
@api_view(["DELETE"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
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
@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Количество откликов для данной вакансии в заявке.",
                example=1
            ),
        },
        required=['count']
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


# PUT пользователя (личный кабинет)

# Домен пользователь
# PUT пользователя (личный кабинет)
@swagger_auto_schema(method='put', request_body=UserSerializer)
@api_view(["PUT"])
@authentication_classes([CsrfExemptSessionAuthentication])
@permission_classes([IsAuthenticated])
def UpdateUser(request, user_id):
    if not User.objects.filter(id=user_id).exists():
        return Response({"detail": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(id=user_id)

    if not request.user.is_superuser:
        if user != request.user:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)

    serializer = UserSerializer(user, data=request.data, many=False, partial=True)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model_class = User

    """def get_authenticators(self):
        if self.action in ['create']:
            authentication_classes = [AllowAny] # Отключаем аутентификацию
        else:
            authentication_classes = [CsrfExemptSessionAuthentication()]  # Используем
        return [authenticate() for authenticate in authentication_classes]"""

    http_method_names = ['create', 'list', 'get', 'post', 'delete']

    def get_permissions(self):
        if self.action in ['create']:
            permission_class = [AllowAny]
        elif self.action in ['list']:
            permission_class = [IsManager | IsAdmin ]
        else:
            permission_class = [IsAdmin]
        return [permission() for permission in permission_class]

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
        response.set_cookie('session_id', random_key)
        return response
    else:
        return Response(
            {"success": False, "error": "Неверное имя пользователя или пароль."},
            status=status.HTTP_400_BAD_REQUEST
        )


#@csrf_exempt
@api_view(['POST'])
#@permission_classes([IsAuthenticated])
#@authentication_classes([CsrfExemptSessionAuthentication])
def logout_view(request):

    session_id = request.COOKIES.get('session_id')

    if session_id:
        session_storage.delete(session_id)

        response = Response({'status': 'Success'}, status=200)
        response.delete_cookie('session_id')

        logout(request)

        request.user = AnonymousUser()
        console.log(session_id)
        return response
    else:
        return Response({'status': 'Error', 'message': 'No active session'}, status=400)


# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)