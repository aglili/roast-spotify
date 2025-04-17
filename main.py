from dotenv import load_dotenv
import os
from fastapi import  FastAPI
from starlette.middleware.sessions import SessionMiddleware

from routes import router

load_dotenv()

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

app = FastAPI(title="roast spotify api")

app.add_middleware(SessionMiddleware,secret_key=APP_SECRET_KEY)




app.include_router(router=router,prefix="/api/v1")





