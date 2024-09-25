from django.shortcuts import render

companies = [
    {
        "id": 1,
        "name": "Водитель курьер",
        "description": "Требуемый опыт работы: не требуется\nЧастичная занятость, гибкий график\nВозможно временное оформление: договор услуг, подряда, ГПХ, самозанятые, ИПХ\nВозможна подработка: сменами по 4-6 часов",
        "image": "http://localhost:9000/images/1.png",
        "money": "от 180 000 ₽ до 220 000 на руки",
        "city": "Москва",
        "name_company": "Купер",
        "peculiarities": "Нарушение слуха",
    },
    {
        "id": 2,
        "name": "Оператор контакт-центра",
        "description": "Требуемый опыт работы: 1-2 года\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/2.png",
        "money": "от 35 000 ₽ до 50 000 на руки",
        "city": "Москва",
        "name_company": "Контакт Плюс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 3,
        "name": "Консультант по продажам",
        "description": "Требуемый опыт работы: не требуется\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/3.png",
        "money": "от 40 000 ₽ до 55 000 на руки",
        "city": "Санкт-Петербург",
        "name_company": "Консалтинг Экспресс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 4,
        "name": "Онлайн-переводчик",
        "description": "Требуемый опыт работы: 1-3 года\nГибкий график, удаленная работа\nОформление по ГПХ",
        "image": "http://localhost:9000/images/4.png",
        "money": "от 45 000 ₽ до 70 000 на руки",
        "city": "Москва",
        "name_company": "Бюро Переводов",
        "peculiarities": "Работа подходит для людей с нарушениями слуха"
    },
    {
        "id": 5,
        "name": "Оператор call-центра",
        "description": "Требуемый опыт работы: 1-2 года\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/5.png",
        "money": "от 35 000 ₽ до 50 000 на руки",
        "city": "Екатеринбург",
        "name_company": "Колл Центр",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 6,
        "name": "Оператор ПК",
        "description": "Требуемый опыт работы: не требуется\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/6.png",
        "money": "от 30 000 ₽ до 45 000 на руки",
        "city": "Новосибирск",
        "name_company": "Офис Плюс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
]

draft_vacancy = {
    "id": 123,
    "date_created": "12 сентября 2024г",
    "companies": [
        {
            "id": 1,
            "name": "Водитель курьер",
            "description": "Требуемый опыт работы: не требуется\nЧастичная занятость, гибкий график\nВозможно временное оформление: договор услуг, подряда, ГПХ, самозанятые, ИПХ\nВозможна подработка: сменами по 4-6 часов",
            "image": "http://localhost:9000/images/1.png",
            "money": "от 180 000 ₽ до 220 000 на руки",
            "city": "Москва",
            "name_company": "Купер",
            "peculiarities": "Нарушение слуха",
        },
        {
            "id": 2,
            "name": "Оператор контакт-центра",
            "description": "Требуемый опыт работы: 1-2 года\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
            "image": "http://localhost:9000/images/2.png",
            "money": "от 35 000 ₽ до 50 000 на руки",
            "city": "Москва",
            "name_company": "Контакт Плюс",
            "peculiarities": "Работа подходит для людей с ограниченными возможностями"
        },
        {
            "id": 3,
            "name": "Консультант по продажам",
            "description": "Требуемый опыт работы: не требуется\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
            "image": "http://localhost:9000/images/3.png",
            "money": "от 40 000 ₽ до 55 000 на руки",
            "city": "Санкт-Петербург",
            "name_company": "Консалтинг Экспресс",
            "peculiarities": "Работа подходит для людей с ограниченными возможностями"
        },
        {
            "id": 4,
            "name": "Онлайн-переводчик",
            "description": "Требуемый опыт работы: 1-3 года\nГибкий график, удаленная работа\nОформление по ГПХ",
            "image": "http://localhost:9000/images/4.png",
            "money": "от 45 000 ₽ до 70 000 на руки",
            "city": "Москва",
            "name_company": "Бюро Переводов",
            "peculiarities": "Работа подходит для людей с нарушениями слуха"
        },
    ]
}


def getVacancyById(company_id):
    for company in companies:
        if company["id"] == company_id:
            return company


def searchVacancies(company_name):
    res = []

    for company in companies:
        if company_name.lower() in company["name"].lower():
            res.append(company)

    return res


def getDraftResponse():
    return draft_vacancy


def getResponseById(vacancy_id):
    return draft_vacancy


def index(request):
    name = request.GET.get("name", "")
    companies = searchVacancies(name)
    draft_vacancy = getDraftResponse()

    context = {
        "companies": companies,
        "name": name,
        "companies_count": len(draft_vacancy["companies"]),
        "draft_vacancy": draft_vacancy
    }

    return render(request, "home_page.html", context)


def company(request, company_id):
    context = {
        "id": company_id,
        "vacancy": getVacancyById(company_id),
    }

    return render(request, "vacancy_page.html", context)


def vacancy(request, vacancy_id):
    context = {
        "vacancy": getResponseById(vacancy_id),
    }

    return render(request, "responses.html", context)
