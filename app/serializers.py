from collections import OrderedDict

from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User

# Сериализатор для модели Vacancies
class VacanciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancies
        fields = [
            'vacancy_id', 'vacancy_name', 'description', 'money_from', 'money_to',
            'url', 'city', 'name_company', 'peculiarities'
        ]

class ResponsesSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username', read_only=True)
    moderator = serializers.CharField(source='moderator.username', read_only=True)

    class Meta:
        model = Responses

        fields = '__all__'

        """def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields"""

# Сериализатор для модели ResponsesVacancies (Связь между откликами и вакансиями)
class ResponsesVacanciesSerializer(serializers.ModelSerializer):
    vacancy_id = Vacancies()
    quantity = serializers.IntegerField()
    vacancy_name = serializers.CharField(source='vacancy.vacancy_name')
    money_from = serializers.IntegerField(source='vacancy.money_from')
    money_to = serializers.IntegerField(source='vacancy.money_to')
    url = serializers.CharField(source='vacancy.url')
    city = serializers.CharField(source='vacancy.city')
    name_company = serializers.CharField(source='vacancy.name_company')
    peculiarities = serializers.CharField(source='vacancy.peculiarities')


    class Meta:
        model = ResponsesVacancies
        fields = ["vacancy_id", "vacancy_name", "money_from", "money_to", "url", "city", "name_company", "peculiarities", "request", "quantity"]


    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)  # Получаем список полей из аргументов
        super().__init__(*args, **kwargs)
        if fields is not None:
            # Оставляем только указанные поля
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    """def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields"""

    """def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields"""


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)

    class Meta:
        #model = CustomUser
        #fields = ("id", "email", "password", "first_name", "last_name", "date_joined", "password", "username") # Для PUT пользователя
        model = User
        fields = ("id", "email", "password", "first_name", "last_name", "date_joined", "password", "username", "is_staff", "is_superuser") # Для PUT пользователя


"""
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "date_joined", "username"]
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ["id"]



    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),  # Используем .get() для безопасного доступа
            last_name=validated_data.get('last_name', ''),
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields



# Сериализатор для авторизации пользователя
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields"""