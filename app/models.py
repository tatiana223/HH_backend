from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class Vacancies(models.Model):
    STATUS_CHOICES = [
        (1, 'Действует'),
        (2, 'Удалена')
    ]

    id_vacancy = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    money_from = models.IntegerField(default=0)
    money_to = models.IntegerField(default=0)
    url = models.TextField(max_length=1024, null=True, blank=True)
    city = models.CharField(max_length=255, default='Неизвестно')
    name_company = models.CharField(max_length=255, default='Default company name')
    peculiarities = models.TextField(default='Default company name')

    class Meta:
        managed = True
        db_table = 'vacancies'


class Responses(models.Model):
    STATUS_CHOICES = (
        (1, 'Черновик'),
        (2, 'Удалена'),
        (3, 'Сформирована'),
        (4, 'Завершена'),
        (5, 'Отклонена'),

    )

    id_response = models.AutoField(primary_key=True)  # Автоинкрементное поле
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_responses')
    created_at = models.DateTimeField(auto_now_add=True)
    formed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='moderated_requests', null=True, blank=True)
    name_human = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    peculiarities_comm = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'responses'


class ResponsesVacancies(models.Model):
    mm_id = models.AutoField(primary_key=True)
    request = models.ForeignKey(Responses, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancies, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    order = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'responses_vacancies'
        unique_together = ('request', 'vacancy')

