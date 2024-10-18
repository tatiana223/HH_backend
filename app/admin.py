from django.contrib import admin
from .models import Vacancies
from .models import Responses
from .models import ResponsesVacancies

admin.site.register(Vacancies)
admin.site.register(Responses)
admin.site.register(ResponsesVacancies)

