import asyncio
from aioarango import ArangoClient
from aioarango.database import StandardDatabase

class ArangoDBPool:
    def __init__(
        self,
                db_name: str, 
                username: str, 
                password: str, 
                hosts: str,
                pool_size: int = 500
        ):
        self.client = ArangoClient()
        self.db_name = db_name
        self.username = username
        self.password = password
        self.hosts = hosts
        self.pool_size = pool_size
        self.pool = asyncio.Queue()

    async def initialize_pool(self):
        """Создаёт пул подключений"""
        for _ in range(self.pool_size):
            conn = await self.create_connection()
            await self.pool.put(conn)

    async def create_connection(self) -> StandardDatabase:
        """Создаёт новое подключение к базе ArangoDB"""
        return await self.client.db(
            self.db_name, username=self.username, password=self.password#, hosts=self.hosts
        )

    async def get_connection(self) -> StandardDatabase:
        """Берёт соединение из пула (или ждёт, пока освободится)"""
        return await self.pool.get()

    async def release_connection(self, conn: StandardDatabase):
        """Возвращает соединение в пул"""
        await self.pool.put(conn)

    async def close_pool(self):
        """Закрывает все соединения в пуле"""
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()