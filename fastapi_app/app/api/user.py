from fastapi import APIRouter 

router = APIRouter()

@router.get("/me")
async def get_me():
    return {"message":"hello, world"}

