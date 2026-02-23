from fastapi import FastAPI
import models
from database import engine
from routers import auth, todos

app = FastAPI()


#this is going to run if our todos.db does not exist
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)