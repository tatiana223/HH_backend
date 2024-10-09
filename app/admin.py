from django.contrib import admin
from .models import Vacancies
from .models import Request
from .models import RequestServices

admin.site.register(Vacancies)
admin.site.register(RequestServices)
admin.site.register(Request)

