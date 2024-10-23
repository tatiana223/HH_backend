from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Vacancies, Responses, ResponsesVacancies


# Сериализатор для модели Vacancies
class VacanciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancies
        fields = ['id_vacancy', 'name', 'description', 'money_from', 'money_to', 'image', 'city', 'name_company', 'peculiarities']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False}
        }
class ResponsesSerializer(serializers.ModelSerializer):
    #creator = serializers.CharField(source='creator.username', read_only=True)
    #moderator = serializers.CharField(source='moderator.username', read_only=True)

    class Meta:
        model = Responses
        fields = '__all__'

# Сериализатор для модели ResponsesVacancies (Связь между откликами и вакансиями)
class ResponsesVacanciesSerializer(serializers.ModelSerializer):
    #request = ResponsesSerializer()  # Включаем сериализатор откликов
    vacancy = VacanciesSerializer()  # Включаем сериализатор вакансий
    count_responses = serializers.SerializerMethodField()  # Поле для подсчета откликов

    class Meta:
        model = ResponsesVacancies
        fields = ['mm_id', 'request', 'vacancy', 'quantity', 'order', 'count_responses']

    def get_count_responses(self, obj):
        # Подсчитываем количество откликов для вакансии
        return Responses.objects.filter(id_response=obj.request.id_response).count()

# Сериализатор для пользователей
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']


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



# Сериализатор для авторизации пользователя
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
