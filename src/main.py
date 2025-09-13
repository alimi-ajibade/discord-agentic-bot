from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    pass

    yield


app = FastAPI(
    title="Discord Agentic Bot",
    description="Discord Agentic Bot",
    version="0.0.1",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)
