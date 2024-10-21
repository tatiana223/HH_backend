from django.contrib import admin
from .models import *

admin.site.register(Vacancies)
admin.site.register(Responses)
admin.site.register(ResponsesVacancies)

