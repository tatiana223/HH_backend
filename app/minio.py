from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import Response
from rest_framework import status


def process_file_upload(file_object: InMemoryUploadedFile, client: Minio, image_name: str) -> str:
    """Загружает файл в MinIO и возвращает URL."""
    try:
        client.put_object(
            'images',
            image_name,
            file_object.file,
            file_object.size
        )
        return f"http://{settings.AWS_S3_ENDPOINT_URL}/images/{image_name}"

    except Exception as e:
        return {"error": str(e)}


def add_pic(new_vacancy, pic: InMemoryUploadedFile) -> Response:
    """Добавляет изображение к новому городу и сохраняет его в MinIO."""
    client = Minio(
        endpoint=settings.AWS_S3_ENDPOINT_URL,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        secure=settings.MINIO_USE_SSL
    )

    if not pic:
        return Response({"error": "Нет файла для изображения."}, status=status.HTTP_400_BAD_REQUEST)

    # Генерация уникального имени для изображения
    img_obj_name = f"{new_vacancy.id_vacancy}.png"

    # Процесс загрузки файла
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Сохранение URL-адреса изображения в объекте города
    new_vacancy.image = result
    new_vacancy.save()

    return Response({"message": "Изображение успешно загружено.", "url": result}, status=status.HTTP_201_CREATED)
