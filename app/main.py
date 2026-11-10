"""QuickBite restaurant service: restaurants and their menus."""
import logging
import socket
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("restaurant-service")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="QuickBite Restaurant Service",
    description="Owns restaurants and menus. Other services read menu data through this API.",
    version="1.0.0",
    lifespan=lifespan,
)


def _restaurant_or_404(db: Session, restaurant_id: int) -> models.Restaurant:
    restaurant = db.get(models.Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Restaurant {restaurant_id} not found")
    return restaurant


def _menu_item_or_404(db: Session, item_id: int) -> models.MenuItem:
    item = db.get(models.MenuItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Menu item {item_id} not found")
    return item


@app.get("/health", tags=["ops"])
def health(db: Session = Depends(get_db)):
    """Liveness and readiness check. `served_by` shows which pod answered."""
    db.execute(text("SELECT 1"))
    return {"service": "restaurant-service", "status": "UP", "served_by": socket.gethostname()}


# ---------- commands ----------

@app.post("/restaurants", response_model=schemas.RestaurantOut, status_code=status.HTTP_201_CREATED, tags=["restaurants"])
def register_restaurant(payload: schemas.RestaurantCreate, db: Session = Depends(get_db)):
    restaurant = models.Restaurant(**payload.model_dump())
    db.add(restaurant)
    db.commit()
    log.info("restaurant registered id=%s name=%s", restaurant.id, restaurant.name)
    return restaurant


@app.patch("/restaurants/{restaurant_id}/status", response_model=schemas.RestaurantOut, tags=["restaurants"])
def set_restaurant_status(restaurant_id: int, payload: schemas.RestaurantStatusUpdate, db: Session = Depends(get_db)):
    restaurant = _restaurant_or_404(db, restaurant_id)
    restaurant.is_open = payload.is_open
    db.commit()
    log.info("restaurant id=%s is_open=%s", restaurant.id, restaurant.is_open)
    return restaurant


@app.post(
    "/restaurants/{restaurant_id}/menu-items",
    response_model=schemas.MenuItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["menu"],
)
def add_menu_item(restaurant_id: int, payload: schemas.MenuItemCreate, db: Session = Depends(get_db)):
    _restaurant_or_404(db, restaurant_id)
    item = models.MenuItem(restaurant_id=restaurant_id, **payload.model_dump())
    db.add(item)
    db.commit()
    log.info("menu item added id=%s restaurant=%s", item.id, restaurant_id)
    return item


@app.patch("/menu-items/{item_id}", response_model=schemas.MenuItemOut, tags=["menu"])
def update_menu_item(item_id: int, payload: schemas.MenuItemUpdate, db: Session = Depends(get_db)):
    item = _menu_item_or_404(db, item_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    log.info("menu item updated id=%s", item.id)
    return item


@app.delete("/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["menu"])
def remove_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = _menu_item_or_404(db, item_id)
    db.delete(item)
    db.commit()
    log.info("menu item removed id=%s", item_id)


# ---------- queries ----------

@app.get("/restaurants", response_model=list[schemas.RestaurantOut], tags=["restaurants"])
def list_restaurants(
    city: str | None = Query(default=None, description="Filter by city"),
    cuisine: str | None = Query(default=None, description="Filter by cuisine"),
    db: Session = Depends(get_db),
):
    query = select(models.Restaurant).order_by(models.Restaurant.id)
    if city:
        query = query.where(models.Restaurant.city.ilike(city))
    if cuisine:
        query = query.where(models.Restaurant.cuisine.ilike(cuisine))
    return db.scalars(query).all()


@app.get("/restaurants/{restaurant_id}", response_model=schemas.RestaurantDetail, tags=["restaurants"])
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Restaurant with its full menu. The order service calls this to validate an order."""
    return _restaurant_or_404(db, restaurant_id)


@app.get("/restaurants/{restaurant_id}/menu", response_model=list[schemas.MenuItemOut], tags=["menu"])
def get_menu(restaurant_id: int, db: Session = Depends(get_db)):
    return _restaurant_or_404(db, restaurant_id).menu


@app.get("/menu-items/{item_id}", response_model=schemas.MenuItemOut, tags=["menu"])
def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    return _menu_item_or_404(db, item_id)
