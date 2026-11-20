import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.generated_test import GeneratedTest, TestExecution
from app.services.sandbox.docker_runner import run_tests_in_sandbox


async def execute_generated_test(
    execution_id: uuid.UUID, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as db:
        execution = await db.get(TestExecution, execution_id)
        if execution is None:
            return

        generated_test = await db.get(GeneratedTest, execution.generated_test_id)
        if generated_test is None:
            execution.status = "failed"
            execution.output = "Generated test no longer exists."
            await db.commit()
            return

        execution.status = "running"
        await db.commit()

        # docker-py's calls are blocking network I/O to the Docker daemon; run them
        # off the event loop rather than stalling it for the duration of the test.
        result = await asyncio.to_thread(
            run_tests_in_sandbox, generated_test.framework, generated_test.code
        )

        execution.status = result.status
        execution.output = result.output
        execution.duration_ms = result.duration_ms
        await db.commit()
