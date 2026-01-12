from datetime import datetime
import json
from typing import Any
from collections import deque
from dataclasses import asdict

from coro_runner.enums import TaskStatusEnum
from coro_runner.utils import get_task_name, get_the_func
from coro_runner.types import FutureFuncType
from .base import BaseBackend
from ..schema import MySQLConfig, TaskModel

class MySQLBackend(BaseBackend):
    def __init__(self, conf: MySQLConfig) -> None:
        super().__init__()
        self._conf = conf
        self.pool = None
        self._table_name = "coro_runner_tasks"

    async def _get_pool(self):
        if self.pool is None:
            try:
                import aiomysql
            except ImportError:
                 raise ImportError(
                    "aiomysql is required to use MySQLBackend. Please install it."
                )
            
            self.pool = await aiomysql.create_pool(
                host=self._conf.host, 
                port=self._conf.port,
                user=self._conf.user, 
                password=self._conf.password,
                db=self._conf.db,
                autocommit=True
            )
            # Ensure table exists
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(f'''
                        CREATE TABLE IF NOT EXISTS {self._table_name} (
                            task_id VARCHAR(36) PRIMARY KEY,
                            name VARCHAR(255),
                            module VARCHAR(255),
                            queue VARCHAR(255),
                            received DATETIME,
                            status INT,
                            args JSON,
                            kwargs JSON,
                            result TEXT,
                            started DATETIME,
                            finished DATETIME,
                            exception TEXT,
                            remark TEXT
                        )
                    ''')
        return self.pool

    async def add_task_to_db(
        self,
        queue_name: str,
        task: FutureFuncType,
        args: list | tuple = [],
        kwargs: dict = {},
    ) -> TaskModel:
        try:
            json_args = json.dumps(list(args), default=str)
            json_kwargs = json.dumps(kwargs, default=str)
        except (TypeError, OverflowError):
             raise ValueError("Arguments must be JSON serializable while using persistent backend.")

        task_data = TaskModel(
            name=get_task_name(task),
            module=task.__module__,
            queue=queue_name,
            received=datetime.now(),
            args=list(args),
            kwargs=kwargs,
        )
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"INSERT INTO {self._table_name} (task_id, name, module, queue, received, status, args, kwargs) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (task_data.task_id, task_data.name, task_data.module, task_data.queue, task_data.received, task_data.status, json_args, json_kwargs)
                )
        return task_data

    async def update_task_in_db(
        self,
        task_id: str,
        **updates: Any,
    ) -> TaskModel | None:
        
        # Build query
        set_clauses = []
        values = []
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
            
        if not set_clauses:
            return await self.get_task_from_db(task_id)
            
        values.append(task_id)
        
        query = f"UPDATE {self._table_name} SET {', '.join(set_clauses)} WHERE task_id = %s"
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, tuple(values))
                
        return await self.get_task_from_db(task_id)

    async def get_task_from_db(self, task_id: str) -> TaskModel | None:
        import aiomysql
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SELECT * FROM {self._table_name} WHERE task_id = %s", (task_id,))
                row = await cur.fetchone()
                if row:
                    return self._row_to_task_model(row)
        return None

    async def get_all_tasks_from_db(self) -> tuple[list[TaskModel], list[TaskModel], list[TaskModel], list[TaskModel], list[TaskModel]]:
        import aiomysql
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SELECT * FROM {self._table_name}")
                rows = await cur.fetchall()
                
        waitings, runnings, completed, failed, cancelled = [], [], [], [], []
        for row in rows:
            task = self._row_to_task_model(row)
            if task.status == TaskStatusEnum.PENDING.value:
                waitings.append(task)
            elif task.status == TaskStatusEnum.RUNNING.value:
                runnings.append(task)
            elif task.status == TaskStatusEnum.FINISHED.value:
                completed.append(task)
            elif task.status == TaskStatusEnum.FAILED.value:
                failed.append(task)
            elif task.status == TaskStatusEnum.CANCELLED.value:
                cancelled.append(task)
                
        return waitings, runnings, completed, failed, cancelled

    def _row_to_task_model(self, row) -> TaskModel:
        # row is dict
        args = json.loads(row['args']) if isinstance(row['args'], str) else row['args']
        kwargs = json.loads(row['kwargs']) if isinstance(row['kwargs'], str) else row['kwargs']

        if args is None: args = []
        if kwargs is None: kwargs = {}
        
        return TaskModel(
            task_id=row['task_id'],
            name=row['name'],
            module=row['module'],
            queue=row['queue'],
            received=row['received'],
            status=row['status'],
            args=args,
            kwargs=kwargs,
            result=row['result'],
            started=row['started'],
            finished=row['finished'],
            exception=row['exception'],
            remark=row['remark']
        )
