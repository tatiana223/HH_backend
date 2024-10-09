from django.shortcuts import render

companies = [
    {
        "id": 1,
        "name_vacancy": "Водитель курьер",
        "description": "Требуемый опыт работы: не требуется\nЧастичная занятость, гибкий график\nВозможно временное оформление: договор услуг, подряда, ГПХ, самозанятые, ИПХ\nВозможна подработка: сменами по 4-6 часов",
        "image": "http://localhost:9000/images/1.png",
        "money_from": 180000,
        "money_to": 220000,
        "city": "Москва",
        "name_company": "Купер",
        "peculiarities": "Нарушение слуха",
    },
    {
        "id": 2,
        "name_vacancy": "Оператор контакт-центра",
        "description": "Требуемый опыт работы: 1-2 года\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/2.png",
        "money_from": 35000,
        "money_to": 50000,
        "city": "Москва",
        "name_company": "Контакт Плюс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 3,
        "name_vacancy": "Консультант по продажам",
        "description": "Требуемый опыт работы: не требуется\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/3.png",
        "money_from": 40000,
        "money_to": 55000,
        "city": "Санкт-Петербург",
        "name_company": "Консалтинг Экспресс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 4,
        "name_vacancy": "Онлайн-переводчик",
        "description": "Требуемый опыт работы: 1-3 года\nГибкий график, удаленная работа\nОформление по ГПХ",
        "image": "http://localhost:9000/images/4.png",

        "money_from": 45000,
        "money_to": 70000,
        "city": "Москва",
        "name_company": "Бюро Переводов",
        "peculiarities": "Работа подходит для людей с нарушениями слуха"
    },
    {
        "id": 5,
        "name_vacancy": "Оператор call-центра",
        "description": "Требуемый опыт работы: 1-2 года\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/5.png",
        "money_from": 35000,
        "money_to": 50000,
        "city": "Екатеринбург",
        "name_company": "Колл Центр",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
    {
        "id": 6,
        "name_vacancy": "Оператор ПК",
        "description": "Требуемый опыт работы: не требуется\nПолная занятость, гибкий график\nОформление по ТК РФ\nВозможна удаленная работа",
        "image": "http://localhost:9000/images/6.png",
        "money_from": 30000,
        "money_to": 45000,
        "city": "Новосибирск",
        "name_company": "Офис Плюс",
        "peculiarities": "Работа подходит для людей с ограниченными возможностями"
    },
]

draft_vacancy = {
    "id": 123,
    "date_created": "12 сентября 2024г",
     "companies": companies,
}


def getVacancyById(company_id):
    for company in companies:
        if company["id"] == company_id:
            return company


def searchVacancies(company_name):
    res = []

    for company in companies:
        if company_name.lower() in company["name_vacancy"].lower():
            res.append(company)

    return res


def getDraftResponse():
    return draft_vacancy


def getResponseById(vacancy_id):
    return draft_vacancy


def index(request):
    name_vacancy = request.GET.get("name_vacancy", "")
    companies = searchVacancies(name_vacancy)
    draft_vacancy = getDraftResponse()

    context = {
        "companies": companies,
        "name_vacancy": name_vacancy,
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
