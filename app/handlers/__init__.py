import logging

from aiogram import Router
from . import info, menu, referral, sub


router = Router()
logger = logging.getLogger(__name__)


router.include_routers(
    info.router,
    menu.router,
    referral.router,
    sub.router
)