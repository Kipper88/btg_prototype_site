from aioarango.exceptions import DocumentInsertError
from .connection_pool_arango import ArangoDBPool as ConnectionPool

from ...config import (DB_PATH_ENTITIES_ARANGO,
                       DB_PATH_EDGES_ARANGO,
                       DB_PATH_GROUPS_ARANGO)

class ArangoModelEntity:
    def __init__(self, pool: ConnectionPool):
        """Принимаем пул в качестве аргумента."""
        self.pool = pool
        self.entities_collection_name = DB_PATH_ENTITIES_ARANGO
        self.groups_collection_name = DB_PATH_GROUPS_ARANGO
        self.edges_name = DB_PATH_EDGES_ARANGO

    async def create_collection(self, collection_name):
        conn = await self.pool.get_connection()
        try:
            if not await conn.has_collection(collection_name):
                await conn.create_collection(collection_name)
        finally:
            await self.pool.release_connection(conn)

    async def insert_document(self, document):
        """Вставка документа в коллекцию."""
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            return await collection.insert(document)
        except DocumentInsertError as e:
            print(f"Ошибка при вставке документа: {e}")
            return None
        finally:
            await self.pool.release_connection(conn)
            
    async def create_group(self, document):
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.group)
            return await collection.insert(document)
        except DocumentInsertError as e:
            print(f"Ошибка при вставке документа: {e}")
            return None
        finally:
            await self.pool.release_connection(conn)
            
    async def create_entity(self, document):
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            return await collection.insert(document)
        except DocumentInsertError as e:
            print(f"Ошибка при вставке документа: {e}")
            return None
        finally:
            await self.pool.release_connection(conn)

    async def get_documents(self):
        """Получение всех документов из коллекции."""
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            cursor = await collection.all()
            return [doc async for doc in cursor]
        finally:
            await self.pool.release_connection(conn)

    async def get_document_by_id(self, doc_key):
        """Получение документа по ID."""
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            return await collection.get(doc_key)
        finally:
            await self.pool.release_connection(conn)

    async def update_document(self, doc_id, update_data):
        """Обновление документа."""
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            doc = await collection.get(doc_id)
            if doc:
                doc.update(update_data)
                return await collection.update(doc)
            return None
        finally:
            await self.pool.release_connection(conn)

    async def delete_document(self, doc_id):
        """Удаление документа по ID."""
        conn = await self.pool.get_connection()
        try:
            collection = conn.collection(self.entities_collection_name)
            return await collection.delete(doc_id)
        finally:
            await self.pool.release_connection(conn)

    async def create_graph(self, edge_collection_name):
        """Создание графовой и рёберной коллекций."""
        conn = await self.pool.get_connection()
        try:
            #if not await conn.has_collection(graph_name):
            #    await conn.create_collection(graph_name)
            if not await conn.has_collection(edge_collection_name):
                await conn.create_collection(edge_collection_name, edge=True)
        finally:
            await self.pool.release_connection(conn)

    async def create_edge(self, from_doc_id, to_doc_id, edge_collection_name):
        """Создание связи (рёберного документа) между объектами."""
        conn = await self.pool.get_connection()
        try:
            edge_collection = conn.collection(edge_collection_name)
            edge = {"_from": from_doc_id, "_to": to_doc_id}
            return await edge_collection.insert(edge)
        except DocumentInsertError:
            return None
        finally:
            await self.pool.release_connection(conn)

    async def insert_order_data(self, collection_name, data):
        """Вставка данных заказа в коллекцию."""
        document = {
            "_key": str(data["id"]),
            "name": data["name"],
            "settings": data.get("settings", {})
        }
        return await self.insert_document(collection_name, document)

    async def get_edges(self, edge_collection_name):
        """Получение всех рёбер из рёберной коллекции."""
        conn = await self.pool.get_connection()
        try:
            edge_collection = conn.collection(edge_collection_name)
            cursor = await edge_collection.all()
            return [edge async for edge in cursor]
        finally:
            await self.pool.release_connection(conn)
            
    async def get_multilevel_connections(self):
        db = await client.db('your_database', username='root', password='')

        query = """
        FOR v, e, p IN 1..3 OUTBOUND 'users/startUser' friendships
            RETURN { user: v, path: p }
        """

        cursor = await db.aql.execute(query)
        result = [doc async for doc in cursor]

        await client.close()
        return result