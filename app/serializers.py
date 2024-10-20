
from rest_framework import serializers
#from .models import *

class VacanciesSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, vacancy):
        has_response = ResponsesVacancies.objects.filter(vacancy=vacancy, response__status=1).exists()
        return not has_response

    class Meta:
        model = Vacancies
        fields = '__all__'

class ResponsesSerializer(serializers.ModelSerializer):
    vacancy_amount = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_vacancies_amount(self,response):
        return ResponsesVacancies.objects.filter(response=response).count()

    def get_owner(self, response):
        return response.owner.username

    def get_moderator(self, response):
        if response.moderator:
            return response.moderator.username
        return None  # Возвращаем None, если модератора нет

    class Meta:
        model = Responses
        fields = '__all__'

class ResponsesVacanciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponsesVacancies
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'date_joined', 'password', 'username')


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
