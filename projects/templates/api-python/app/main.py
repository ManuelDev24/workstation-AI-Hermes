from fastapi import FastAPI
from pydantic import BaseModel, Field

from .config import settings

app = FastAPI(title="API template")
_items: list[dict] = []


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/items", status_code=201)
def create_item(item: ItemIn) -> dict:
    if len(_items) >= settings.max_items:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail="límite de items alcanzado")
    _items.append(item.model_dump())
    return item.model_dump()


@app.get("/items")
def list_items() -> list[dict]:
    return _items
