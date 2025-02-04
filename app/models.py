from django.db import models
from django.contrib.auth.models import User
import django.contrib.auth.models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from datetime import timedelta


class Vacancies(models.Model):
    STATUS_CHOICES = [
        (1, 'Действует'),
        (2, 'Удалена')
    ]
    vacancy_id = models.AutoField(primary_key=True)
    vacancy_name = models.CharField(max_length=255)
    description = models.TextField()
    money_from = models.IntegerField(default=0)
    money_to = models.IntegerField(default=0)
    url = models.TextField(max_length=1024, null=True, blank=True)
    city = models.CharField(max_length=255, default='Неизвестно')
    name_company = models.CharField(max_length=255, default='Default company name')
    peculiarities = models.TextField(default='Default company name')
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, blank=False, null=False)

    class Meta:
        managed = True
        db_table = 'vacancies'


class Responses(models.Model):
    STATUS_CHOICES = [
        (1, 'Черновик'),
        (2, 'Удалена'),
        (3, 'Сформирована'),
        (4, 'Завершена'),
        (5, 'Отклонена'),
    ]

    id_response = models.AutoField(primary_key=True)  # Автоинкрементное поле
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    creator = models.ForeignKey(django.contrib.auth.models.User, on_delete=models.CASCADE, related_name='created_responses')
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    moderator = models.ForeignKey(django.contrib.auth.models.User, on_delete=models.SET_NULL, related_name='moderated_requests', null=True,
                                  blank=True)
    name_human = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    peculiarities_comm = models.TextField(blank=True, null=True)
    vacancies = models.ManyToManyField('Vacancies', through='ResponsesVacancies', blank=True)  # Связь с вакансиями
    interview_date = models.DateTimeField(null=True, blank=True)  # Поле для даты собеседования

    qr = models.TextField(null=True, blank=True)
    def save(self, *args, **kwargs):
        # Установить дату собеседования, если она не задана
        if not self.interview_date:
            self.interview_date = self.created_at + timedelta(days=30)
        super().save(*args, **kwargs)

    class Meta:
        managed = True
        db_table = 'responses'


class ResponsesVacancies(models.Model):
    mm_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(Responses, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancies, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)



    class Meta:
        managed = True
        db_table = 'responses_vacancies'
        unique_together = ('request', 'vacancy')


