from pydantic import BaseModel, ConfigDict, Field


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price: float = Field(gt=0)
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    price: float | None = Field(default=None, gt=0)
    is_available: bool | None = None


class MenuItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    name: str
    price: float
    is_available: bool


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    cuisine: str = Field(min_length=1, max_length=60)
    city: str = Field(min_length=1, max_length=60)
    is_open: bool = True


class RestaurantStatusUpdate(BaseModel):
    is_open: bool


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    cuisine: str
    city: str
    is_open: bool


class RestaurantDetail(RestaurantOut):
    menu: list[MenuItemOut] = []
