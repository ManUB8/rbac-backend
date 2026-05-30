from fastapi import APIRouter

from .delete import router as delete_router
from .get import router as get_router
from .patch import router as patch_router
from .post import router as post_router


router = APIRouter(prefix="/activity/v1", tags=["Activity"])
router.include_router(post_router)
router.include_router(get_router)
router.include_router(patch_router)
router.include_router(delete_router)
