from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views import View
from django import template
from django.contrib.auth import authenticate, login, logout
import json
import asyncio
from asgiref.sync import sync_to_async
from django.middleware.csrf import get_token
from .forms import CreateGroupForm, CreateEntityForm
from .database.PostgreSQL.database_postgreSQL import PostgreModelEntity
from .constants import *
from sqlalchemy import text
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import re
import logging
from logging.handlers import RotatingFileHandler

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def is_valid_table_name(name):
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) and len(name) <= 63)

try:
    db_conn_pg = PostgreModelEntity("postgresql+asyncpg://postgres:1234@localhost/entities_data")
except Exception as e:
    logger.error(f"Ошибка инициализации подключения к БД: {str(e)}")
    raise

async_render = sync_to_async(render)
async_render_to_string = sync_to_async(render_to_string)

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")

class PublicAsyncView(View):
    async def dispatch(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower(), None)
        if handler and asyncio.iscoroutinefunction(handler):
            try:
                return await handler(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в dispatch: {str(e)}")
                return JsonResponse({"status": "error", "message": "Внутренняя ошибка сервера"}, status=500)
        return await super().dispatch(request, *args, **kwargs)

class AsyncView(View):
    async def dispatch(self, request, *args, **kwargs):
        is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
        if not is_authenticated:
            return HttpResponseRedirect(redirect_to='/login/')
        handler = getattr(self, request.method.lower(), None)
        if handler and asyncio.iscoroutinefunction(handler):
            try:
                return await handler(request, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в dispatch: {str(e)}")
                return JsonResponse({"status": "error", "message": "Внутренняя ошибка сервера"}, status=500)
        return await super().dispatch(request, *args, **kwargs)

class Entity:
    class IndexView(PublicAsyncView):
        async def get(self, request):
            try:
                is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
                if not is_authenticated:
                    return HttpResponseRedirect(redirect_to='/login/')
                
                entities = await db_conn_pg.fetch_data(table_name="entities", limit=100)
                entities_list = [dict(entity) for entity in entities] if entities else []
                for entity in entities_list:
                    entity["id"] = str(entity.get("id", ""))
                
                response = await async_render(
                    request, 
                    "index.html", 
                    {"entities": entities_list, "title_page": "BTG"}
                )
                csrf_token = await sync_to_async(get_token)(request)
                response.set_cookie('csrftoken', csrf_token, max_age=31449600, secure=False, httponly=False, samesite='Lax')
                return response
            except Exception as e:
                logger.error(f"Ошибка в IndexView: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка обработки запроса"}, status=500)

    class CreateGroup(AsyncView):
        async def get(self, request):
            try:
                form = await sync_to_async(CreateGroupForm)()
                html = await async_render_to_string(
                    "entities/form.html", 
                    {"form": form, "title_form": TEXT_TITLE_FORM_CREATE_ENTITY, "url": "entity/create-group/"}
                )
                return JsonResponse({"html": html})
            except Exception as e:
                logger.error(f"Ошибка в CreateGroup GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка формирования формы"}, status=500)

        async def post(self, request):
            try:
                form = await sync_to_async(CreateEntityForm)(request.POST)
                is_valid = await sync_to_async(lambda: form.is_valid())()
                if not is_valid:
                    errors = await sync_to_async(lambda: form.errors.as_json())()
                    return JsonResponse({"status": "error", "message": f"Неверные данные формы: {errors}"}, status=400)
                
                entity_data = {
                    "name": (await sync_to_async(lambda: form.cleaned_data["name"])()).strip(),
                    "sort": int(await sync_to_async(lambda: form.cleaned_data["sort"])()),
                }
                
                if not entity_data["name"]:
                    return JsonResponse({"status": "error", "message": "Имя не может быть пустым"}, status=400)
                
                await db_conn_pg.insert_data(table_name="entities", data=entity_data)
                return JsonResponse({"status": "success", "message": "Успешно создано"})
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Неверный формат данных: {str(e)}"}, status=400)
            except Exception as e:
                logger.error(f"Ошибка в CreateGroup POST: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка создания группы"}, status=500)

    class CreateEntity(AsyncView):
        async def get(self, request):
            try:
                form = await sync_to_async(CreateEntityForm)()
                html = await async_render_to_string(
                    "entities/form.html", 
                    {"form": form, "title_form": TEXT_TITLE_FORM_CREATE_ENTITY, "url": "entity/create-entity/"}
                )
                return JsonResponse({"html": html})
            except Exception as e:
                logger.error(f"Ошибка в CreateEntity GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка формирования формы"}, status=500)

        async def post(self, request):
            try:
                body = await sync_to_async(lambda: request.body)()
                if not body:
                    return JsonResponse({"status": "error", "message": "Пустое тело запроса"}, status=400)
                
                data = json.loads(body)
                form = await sync_to_async(CreateEntityForm)(data)
                is_valid = await sync_to_async(lambda: form.is_valid())()
                if not is_valid:
                    errors = await sync_to_async(lambda: form.errors.as_json())()
                    return JsonResponse({"status": "error", "message": f"Неверные данные формы: {errors}"}, status=400)

                table_name = await db_conn_pg.create_entity_table()
                if not is_valid_table_name(table_name):
                    return JsonResponse({"status": "error", "message": "Недопустимое имя таблицы"}, status=400)
                
                entity_data = {
                    "tech_entity_name": table_name,
                    "entity_name": (await sync_to_async(lambda: form.cleaned_data.get("name", ""))()).strip()
                }
                
                if not entity_data["entity_name"]:
                    return JsonResponse({"status": "error", "message": "Имя сущности обязательно"}, status=400)
                
                await db_conn_pg.insert_data("entities", entity_data)
                return JsonResponse({"status": "success", "message": f"Сущность создана, таблица: {table_name}"})
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Неверный формат JSON"}, status=400)
            except Exception as e:
                logger.error(f"Ошибка в CreateEntity POST: {str(e)}")
                return JsonResponse({"status": "error", "message": f"Ошибка сервера: {str(e)}"}, status=500)

    class GetEntityOne(AsyncView):
        async def get(self, request):
            try:
                entity_id = await sync_to_async(request.GET.get)("entity_id")
                if not entity_id or not is_valid_table_name(entity_id):
                    return JsonResponse({"status": "error", "message": "Неверный или отсутствующий entity_id"}, status=400)
                
                data = await db_conn_pg.get_table_columns_and_data(table_name=entity_id, limit=100)
                if not data:
                    return JsonResponse({"status": "error", "message": "Сущность не найдена"}, status=404)
                
                form_rows = [row for row in data['columns'] if row not in ["id", "created_at", "created_by", "updated_at"]]
                html = await async_render_to_string(
                    'entities/table-entity-one.html',
                    {"columns": data["columns"], "rows": data["rows"], "form_rows": form_rows, "table_name": entity_id}
                )
                return JsonResponse({"html": html})
            except Exception as e:
                logger.error(f"Ошибка в GetEntityOne: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка получения данных сущности"}, status=500)

    class Manage(AsyncView):
        async def get(self, request):
            try:
                data = await db_conn_pg.fetch_data(table_name="entities", limit=100)
                if data is None:
                    return JsonResponse({"status": "error", "message": "Ошибка получения данных"}, status=500)
                
                rows = [{"entity_name": i["entity_name"], "tech_entity_name": str(i["tech_entity_name"])} for i in data]
                html = await async_render_to_string(
                    'settings_entities/settings_entities.html',
                    {"columns": ["имя", "id"], "rows": rows}
                )
                return JsonResponse({"html": html})
            except Exception as e:
                logger.error(f"Ошибка в Manage GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка получения списка сущностей"}, status=500)

    class Settings(AsyncView):
        async def get(self, request):
            try:
                doc_id = await sync_to_async(request.GET.get)("entity_id")
                if not doc_id or not doc_id.isdigit():
                    return JsonResponse({"status": "error", "message": "Неверный или отсутствующий entity_id"}, status=400)
                
                async with db_conn_pg.get_session() as session:
                    query = text("SELECT * FROM entities WHERE id = :id")
                    result = await session.execute(query, {"id": int(doc_id)})
                    data = result.fetchone()
                
                if not data:
                    return JsonResponse({"status": "error", "message": "Сущность не найдена"}, status=404)
                
                data_dict = dict(data)
                html = await async_render_to_string(
                    'settings_entities/settings-entities_page.html',
                    {"columns": ["имя", "id"], "rows": data_dict.get("data", [])}
                )
                return JsonResponse({"html": html})
            except ValueError:
                return JsonResponse({"status": "error", "message": "Неверный формат entity_id"}, status=400)
            except Exception as e:
                logger.error(f"Ошибка в Settings GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка получения настроек сущности"}, status=500)

    class SettingsEntity(AsyncView):
        async def get(self, request):
            try:
                entity_id = await sync_to_async(request.GET.get)("entity_id")
                if not entity_id or not is_valid_table_name(entity_id):
                    return JsonResponse({"status": "error", "message": "Неверный или отсутствующий entity_id"}, status=400)
                
                columns_data = await db_conn_pg.get_table_columns(entity_id)
                columns = columns_data["columns"]
                
                html = await async_render_to_string(
                    'settings_entities/settings_entity.html',
                    {"columns": columns, "table_name": entity_id}
                )
                return JsonResponse({"html": html})
            except Exception as e:
                logger.error(f"Ошибка в SettingsEntity GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка получения структуры таблицы"}, status=500)

        async def post(self, request):
            try:
                entity_id = await sync_to_async(request.GET.get)("entity_id")
                if not entity_id or not is_valid_table_name(entity_id):
                    return JsonResponse({'success': False, 'error': 'Неверный или отсутствующий entity_id'}, status=400)

                action = await sync_to_async(request.POST.get)('action')
                if action not in ['add_column', 'drop_column']:
                    return JsonResponse({'success': False, 'error': 'Недопустимое действие'}, status=400)

                async with db_conn_pg.get_session() as session:
                    check_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)")
                    result = await session.execute(check_query, {"table_name": entity_id})
                    table_exists = result.scalar()
                    if not table_exists:
                        return JsonResponse({'success': False, 'error': f'Таблица {entity_id} не существует'}, status=404)

                    if action == 'add_column':
                        column_names = await sync_to_async(request.POST.getlist)('column_name[]')
                        column_types = await sync_to_async(request.POST.getlist)('column_type[]')

                        if not column_names or not column_types or len(column_names) != len(column_types):
                            return JsonResponse({'success': False, 'error': 'Неверные данные формы'}, status=400)
                        
                        type_mapping = {
                            "string": "VARCHAR(255)",
                            "integer": "INTEGER",
                            "json": "JSONB",
                            "timestamp": "TIMESTAMP",
                        }
                        for name, type_ in zip(column_names, column_types):
                            type__ = type_mapping[type_]
                            if not is_valid_table_name(name):
                                return JsonResponse({'success': False, 'error': f'Недопустимое имя колонки: {name}'}, status=400)
                            if type__ not in ['VARCHAR(255)', 'INTEGER', 'TEXT', 'BOOLEAN', 'TIMESTAMP']:
                                return JsonResponse({'success': False, 'error': f'Недопустимый тип данных: {type__}'}, status=400)
                            await db_conn_pg.add_column(entity_id, name, type_)

                        await session.commit()
                        return JsonResponse({'success': True, 'message': 'Колонки успешно добавлены'})

                    elif action == 'drop_column':
                        column_names = await sync_to_async(request.POST.getlist)('column_name[]')
                        if not column_names:
                            return JsonResponse({'success': False, 'error': 'Не выбраны колонки для удаления'}, status=400)

                        for name in column_names:
                            if not is_valid_table_name(name):
                                return JsonResponse({'success': False, 'error': f'Недопустимое имя колонки: {name}'}, status=400)
                            await db_conn_pg.drop_column(entity_id, name)

                        await session.commit()
                        return JsonResponse({'success': True, 'message': 'Колонки успешно удалены'})

            except SQLAlchemyError as e:
                if 'session' in locals():
                    await session.rollback()
                logger.error(f"Ошибка БД в SettingsEntity POST: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Ошибка базы данных: {str(e)}'}, status=500)
            except Exception as e:
                if 'session' in locals():
                    await session.rollback()
                logger.error(f"Ошибка в SettingsEntity POST: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Неизвестная ошибка: {str(e)}'}, status=500)

    class AddRecord(AsyncView):
        async def post(self, request):
            try:
                entity_id = await sync_to_async(request.GET.get)("entity_id")
                if not entity_id or not is_valid_table_name(entity_id):
                    return JsonResponse({'success': False, 'error': 'Неверный или отсутствующий entity_id'}, status=400)

                form_data = await sync_to_async(lambda: request.POST)()
                if not form_data:
                    return JsonResponse({'success': False, 'error': 'Отсутствуют данные формы'}, status=400)

                base_columns = ["created_at", "created_by", "updated_at"]
                dynamic_columns = [col for col in form_data.keys() if col not in base_columns]
                
                if not dynamic_columns:
                    return JsonResponse({'success': False, 'error': 'Нет данных для записи'}, status=400)

                values = {}
                for column in dynamic_columns:
                    if not is_valid_table_name(column):
                        return JsonResponse({'success': False, 'error': f'Недопустимое имя колонки: {column}'}, status=400)
                    value_list = await sync_to_async(form_data.getlist)(column)
                    if not value_list or not value_list[0]:
                        return JsonResponse({'success': False, 'error': f'Поле {column} не заполнено'}, status=400)
                    values[column] = value_list[0]

                current_time = datetime.now()
                username = await sync_to_async(lambda: request.user.username if request.user.is_authenticated else "system")()
                values.update({
                    "created_at": current_time,
                    "created_by": username,
                    "updated_at": current_time
                })

                async with db_conn_pg.get_session() as session:
                    check_table_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)")
                    table_exists = await session.execute(check_table_query, {"table_name": entity_id})
                    if not table_exists.scalar():
                        return JsonResponse({'success': False, 'error': f'Таблица {entity_id} не существует'}, status=404)

                    columns_str = ', '.join(f'"{col}"' for col in values.keys())
                    placeholders = ', '.join(f':{col}' for col in values.keys())
                    query = text(f"INSERT INTO \"{entity_id}\" ({columns_str}) VALUES ({placeholders})")
                    
                    await session.execute(query, values)
                    await session.commit()

                return JsonResponse({'success': True})
            except SQLAlchemyError as e:
                if 'session' in locals():
                    await session.rollback()
                logger.error(f"Ошибка БД в AddRecord: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Ошибка базы данных: {str(e)}'}, status=500)
            except Exception as e:
                if 'session' in locals():
                    await session.rollback()
                logger.error(f"Ошибка в AddRecord: {str(e)}")
                return JsonResponse({'success': False, 'error': f'Неизвестная ошибка: {str(e)}'}, status=500)


class Login(PublicAsyncView):
        async def get(self, request):
            try:
                is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
                if is_authenticated:
                    return HttpResponseRedirect(redirect_to='/')
                html = await async_render(request, "login.html", {"title": "Вход"})
                return html
            except Exception as e:
                logger.error(f"Ошибка в Login GET: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка загрузки страницы входа"}, status=500)

        async def post(self, request):
            try:
                username = await sync_to_async(request.POST.get)("username")
                password = await sync_to_async(request.POST.get)("password")
                if not username or not password:
                    return JsonResponse({"status": "error", "message": "Укажите имя пользователя и пароль"}, status=400)
                
                user = await sync_to_async(authenticate)(request=request, username=username, password=password)
                if user is not None:
                    await sync_to_async(login)(request, user)
                    return JsonResponse({"status": "success", "message": "Успешный вход", "redirect": "/"})
                else:
                    return JsonResponse({"status": "error", "message": "Неверные учетные данные"}, status=401)
            except Exception as e:
                logger.error(f"Ошибка в Login POST: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка при входе"}, status=500)

class Logout(PublicAsyncView):
        async def get(self, request):
            try:
                await sync_to_async(logout)(request)
                return HttpResponseRedirect(redirect_to='/login/')
            except Exception as e:
                logger.error(f"Ошибка в Logout: {str(e)}")
                return JsonResponse({"status": "error", "message": "Ошибка при выходе"}, status=500)