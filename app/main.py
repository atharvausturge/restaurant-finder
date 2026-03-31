from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import restaurants, menus, recommendation, discovery

app = FastAPI(title="Tavio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(restaurants.router)
app.include_router(menus.router)
app.include_router(recommendation.router)
app.include_router(discovery.router)
