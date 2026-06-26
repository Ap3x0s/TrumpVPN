from fastapi import APIRouter

from app.api import auth, cabinet, payments, public, subscription

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(payments.router)
api_router.include_router(cabinet.router)
api_router.include_router(subscription.router)
