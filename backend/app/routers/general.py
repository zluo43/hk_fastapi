from fastapi import APIRouter

# Create an APIRouter instance. This is what main.py is looking for.
router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Hello from the General Router!"}

@router.get("/about")
async def about():
    return {"message": "This is a FastAPI app organized with APIRouter."}