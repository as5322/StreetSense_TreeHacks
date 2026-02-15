from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import routing, social, heatmap, location_summary
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing.router)
app.include_router(social.router)
app.include_router(heatmap.router)
app.include_router(location_summary.router)
