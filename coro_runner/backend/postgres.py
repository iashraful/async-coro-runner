from datetime import datetime
import json
from typing import Any
from collections import deque

from coro_runner.enums import TaskStatusEnum
from coro_runner.utils import get_task_name, get_the_func
from coro_runner.types import FutureFuncType
from .base import BaseBackend
from ..schema import PGConfig, TaskModel

class PostgresBackend(BaseBackend):
    def __init__(self, conf: PGConfig) -> None:
        super().__init__()
        self._conf = conf
        self.pool = None
        self._table_name = "coro_runner_tasks"

    async def _get_pool(self):
        if self.pool is None:
            try:
                import asyncpg
            except ImportError:
                 raise ImportError(
                    "asyncpg is required to use PostgresBackend. Please install it."
                )
            
            self.pool = await asyncpg.create_pool(
                host=self._conf.host, 
                port=self._conf.port,
                user=self._conf.user, 
                password=self._conf.password,
                database=self._conf.db
            )
            
            async with self.pool.acquire() as conn:
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        task_id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(255),
                        module VARCHAR(255),
                        queue VARCHAR(255),
                        received TIMESTAMP,
                        status INT,
                        args JSONB,
                        kwargs JSONB,
                        result TEXT,
                        started TIMESTAMP,
                        finished TIMESTAMP,
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
             raise ValueError("Arguments must be JSON serializable when using a persistent backend.")

        task_data = TaskModel(
            name=get_task_name(task),
            module=task.__module__,
            queue=queue_name,
            received=datetime.now(),
            args=list(args),
            kwargs=kwargs,
        )
        
        # asyncpg requires JSON args to be string unless configured otherwise? 
        # Actually it handles JSONB if we pass string.
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self._table_name} (task_id, name, module, queue, received, status, args, kwargs) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                task_data.task_id, task_data.name, task_data.module, task_data.queue, task_data.received, task_data.status, json_args, json_kwargs
            )
        return task_data

    async def update_task_in_db(
        self,
        task_id: str,
        **updates: Any,
    ) -> TaskModel | None:
        
        set_clauses = []
        values = []
        i = 1
        for key, value in updates.items():
            set_clauses.append(f"{key} = ${i}")
            values.append(value)
            i += 1
            
        if not set_clauses:
             return await self.get_task_from_db(task_id)
             
        values.append(task_id)
        query = f"UPDATE {self._table_name} SET {', '.join(set_clauses)} WHERE task_id = ${i}"
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(query, *values)
            
        return await self.get_task_from_db(task_id)

    async def get_task_from_db(self, task_id: str) -> TaskModel | None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT * FROM {self._table_name} WHERE task_id = $1", task_id)
            if row:
                return self._row_to_task_model(row)
        return None

    async def get_all_tasks_from_db(self) -> tuple[list[TaskModel], list[TaskModel], list[TaskModel], list[TaskModel], list[TaskModel]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM {self._table_name}")
                
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
        args = json.loads(row['args'])
        kwargs = json.loads(row['kwargs'])
        
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
