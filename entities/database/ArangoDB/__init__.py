from asyncio import get_event_loop
from ..ArangoDB.connection_pool_arango import ArangoDBPool
from ...config import (
    db_name_arango as db_name,
    db_username_arango as db_username,
    db_pass_arango as db_pass,
    db_host_arango as db_hosts,
    db_pool_size_arango as pool_size
)

pool = ArangoDBPool(
    db_name=db_name, 
    username=db_username, 
    password=db_pass, 
    hosts=db_hosts, 
    pool_size=pool_size,
)

loop = get_event_loop()
loop.create_task(pool.initialize_pool()
)
