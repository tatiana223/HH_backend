import segno
import base64
from io import BytesIO
from datetime import datetime
from app.models import Responses

def generate_response_qr(response):
    """Генерирует QR-код для отклика на вакансию"""
    status_dict = dict(Responses.STATUS_CHOICES)

    # Формируем текст для QR-кода
    info = (
        f"Отклик №{response.id_response}\n"
        f"Создатель: {response.creator.username}\n"
        f"Статус: {status_dict.get(response.status, 'Неизвестен')}\n"
    )

    # Добавляем сведения о вакансиях
    vacancies = response.vacancies.all()
    if vacancies.exists():
        info += "\nВакансии:\n"
        for vacancy in vacancies:
            info += f"- {vacancy.vacancy_name} ({vacancy.city})\n"

    # Добавляем дополнительную информацию
    info += (
        f"\nДата создания: {response.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    if response.interview_date:
        info += f"Дата собеседования: {response.interview_date.strftime('%Y-%m-%d %H:%M:%S')}\n"

    print(info)
    # Генерация QR-кода
    qr = segno.make(info)
    buffer = BytesIO()
    qr.save(buffer, kind='png')
    buffer.seek(0)


    # Конвертация в base64
    qr_image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    print(qr_image_base64)

    return qr_image_base64
