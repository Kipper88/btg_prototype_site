from typing import Dict, Any, List
from sqlalchemy import Table, Column, Integer, String, MetaData, text, TIMESTAMP
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import re

class PostgreModelEntity:
    def __init__(self, database_url: str):
        """
        Инициализация подключения к базе данных.
        
        :param database_url: URL для подключения к базе данных 
                            (например, "postgresql+asyncpg://user:password@localhost/dbname").
        """
        self.engine = create_async_engine(database_url, echo=True, query_cache_size=0)
        self.async_session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для асинхронной сессии."""
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise
            else:
                await session.commit()

    async def get_existing_tables(self) -> List[str]:
        """
        Получает список существующих таблиц в базе данных.
        
        :return: Список имен таблиц.
        """
        async with self.get_session() as session:
            try:
                query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                result = await session.execute(query)
                tables = [row[0] for row in result.fetchall()]
                return tables
            except SQLAlchemyError as e:
                raise ValueError(f"Ошибка получения списка таблиц: {str(e)}")

    async def generate_entity_table_name(self) -> str:
        """
        Генерирует уникальное имя таблицы в формате app_entity_{номер}.
        
        :return: Уникальное имя таблицы.
        """
        tables = await self.get_existing_tables()
        # Ищем таблицы с префиксом app_entity_
        entity_tables = [table for table in tables if table.startswith("app_entity_")]
        
        if not entity_tables:
            return "app_entity_1"
        
        # Извлекаем номера из имен таблиц
        numbers = []
        for table in entity_tables:
            match = re.search(r"app_entity_(\d+)", table)
            if match:
                numbers.append(int(match.group(1)))
        
        # Находим следующий доступный номер
        next_number = max(numbers, default=0) + 1
        return f"app_entity_{next_number}"

    async def create_entity_table(self) -> str:
        """
        Создает новую таблицу для сущности с базовыми полями.
        Имя таблицы генерируется автоматически в формате app_entity_{номер}.
        
        :return: Имя созданной таблицы.
        """
        # Генерируем уникальное имя таблицы
        table_name = await self.generate_entity_table_name()

        # Определяем базовые поля
        columns = {
            "created_at": "timestamp",
            "created_by": "string",
            "updated_at": "timestamp",
        }

        metadata = MetaData()

        # Преобразуем типы данных из строк в классы SQLAlchemy
        type_mapping = {
            "string": String,
            "integer": Integer,
            "json": JSONB,
            "timestamp": TIMESTAMP,
        }

        # Создаем колонки
        table_columns = [Column(name, type_mapping[type_]) for name, type_ in columns.items()]

        # Добавляем колонку id как первичный ключ
        table_columns.insert(0, Column("id", Integer, primary_key=True, autoincrement=True))

        # Создаем таблицу
        table = Table(table_name, metadata, *table_columns)

        # Создаем таблицу в базе данных
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

        return table_name

    async def create_table(self, table_name: str, columns: Dict[str, str]):
        """
        Создает таблицу с указанным именем и колонками.
        
        :param table_name: Имя таблицы.
        :param columns: Словарь, где ключ — имя колонки, значение — тип данных ("string", "integer", "json").
        """
        metadata = MetaData()

        type_mapping = {
            "string": String,
            "integer": Integer,
            "json": JSONB,
            "timestamp": TIMESTAMP,
        }

        table_columns = [Column(name, type_mapping[type_]) for name, type_ in columns.items()]
        table_columns.insert(0, Column("id", Integer, primary_key=True, autoincrement=True))
        table = Table(table_name, metadata, *table_columns)

        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def insert_data(self, table_name: str, data: Dict[str, Any]):
        """
        Вставляет данные в таблицу.
        
        :param table_name: Имя таблицы.
        :param data: Словарь с данными для вставки.
        """
        async with self.get_session() as session:
            try:
                query = text(
                    f"INSERT INTO {table_name} ({', '.join(data.keys())}) "
                    f"VALUES ({', '.join(f':{key}' for key in data.keys())})"
                )
                await session.execute(query, data)
            except SQLAlchemyError as e:
                await session.rollback()
                raise ValueError(f"Ошибка вставки данных: {str(e)}")

    async def fetch_data(self, table_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Извлекает данные из таблицы с ограничением.
        
        :param table_name: Имя таблицы.
        :param limit: Максимальное количество строк.
        :return: Список словарей с данными.
        """
        async with self.get_session() as session:
            try:
                query = text(f"SELECT * FROM {table_name} LIMIT :limit")
                result = await session.execute(query, {"limit": limit})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
            except SQLAlchemyError as e:
                raise ValueError(f"Ошибка получения данных: {str(e)}")
            
    async def get_table_columns_and_data(self, table_name: str, limit: int) -> Dict[str, Any]:
        """
        Получает список колонок таблицы и её данные.

        :param table_name: Имя таблицы.
        :param limit: Максимальное количество строк данных.
        :return: Словарь с ключами 'columns' (список имен колонок) и 'rows' (список данных).
        """
        async with self.get_session() as session:
            try:
                # Получение списка колонок
                columns_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                """)
                columns_result = await session.execute(columns_query, {"table_name": table_name})
                columns = [row[0] for row in columns_result.fetchall()]
                
                if not columns:
                    raise ValueError(f"Таблица {table_name} не найдена или не содержит колонок")

                # Получение данных
                data_query = text(f"SELECT * FROM {table_name} LIMIT :limit")
                data_result = await session.execute(data_query, {"limit": limit})
                rows = [dict(row._mapping) for row in data_result.fetchall()]

                return {
                    "columns": columns,
                    "rows": rows
                }
            except SQLAlchemyError as e:
                raise ValueError(f"Ошибка получения колонок и данных: {str(e)}")
            
    async def get_table_columns(self, table_name: str) -> Dict[str, any]:
        async with self.get_session() as session:
            try:
                # Получение списка колонок
                columns_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                """)
                columns_result = await session.execute(columns_query, {"table_name": table_name})
                columns = [row[0] for row in columns_result.fetchall()]
                
                if not columns:
                    raise ValueError(f"Таблица {table_name} не найдена или не содержит колонок")
                
                return {
                    "columns": columns
                }
            except SQLAlchemyError as e:
                raise ValueError(f"Ошибка получения колонок и данных: {str(e)}")

    async def update_data(self, table_name: str, record_id: int, data: Dict[str, Any]):
        """
        Обновляет запись в таблице.
        
        :param table_name: Имя таблицы.
        :param record_id: ID записи для обновления.
        :param data: Словарь с данными для обновления.
        """
        async with self.get_session() as session:
            try:
                set_clause = ", ".join(f"{key} = :{key}" for key in data.keys())
                query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id")
                await session.execute(query, {**data, "id": record_id})
            except SQLAlchemyError as e:
                await session.rollback()
                raise ValueError(f"Ошибка обновления данных: {str(e)}")




    async def add_column(self, table_name: str, column_name: str, column_type: str):
        """
        Добавляет новую колонку в таблицу.
        
        :param table_name: Имя таблицы.
        :param column_name: Имя новой колонки.
        :param column_type: Тип новой колонки ("string", "integer", "json", "timestamp").
        """
        type_mapping = {
            "string": "VARCHAR(255)",
            "integer": "INTEGER",
            "json": "JSONB",
            "timestamp": "TIMESTAMP",
        }
        if column_type not in type_mapping:
            raise ValueError(f"Недопустимый тип колонки: {column_type}")
        
        if not column_name.isidentifier():
            raise ValueError(f"Некорректное имя колонки: {column_name}")
        
        async with self.get_session() as session:
            try:
                check_query = text("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_schema = CURRENT_SCHEMA() 
                        AND table_name = :table_name 
                        AND column_name = :column_name
                    )
                """)
                result = await session.execute(check_query, {"table_name": table_name, "column_name": column_name})
                
                if result.scalar():
                    raise ValueError(f"Колонка '{column_name}' уже существует в таблице '{table_name}'")
                
                query = text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {type_mapping[column_type]}")
                await session.execute(query)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise ValueError(f"Ошибка добавления колонки: {str(e)}")

    async def drop_column(self, table_name: str, column_name: str):
        """
        Удаляет колонку из таблицы.
        
        :param table_name: Имя таблицы.
        :param column_name: Имя колонки для удаления.
        """
        async with self.get_session() as session:
            try:
                query = text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
                await session.execute(query)
            except SQLAlchemyError as e:
                await session.rollback()
                raise ValueError(f"Ошибка удаления колонки: {str(e)}")