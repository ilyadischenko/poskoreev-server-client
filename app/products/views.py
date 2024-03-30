from fastapi import HTTPException, APIRouter, Response, Request

from app.products.models import Product, Menu, ProductCategory

products_router = APIRouter(
    prefix="/api/v1/products"
)


@products_router.get('/', tags=['Products'])
async def get_products(request: Request):
    if '_ri' not in request.cookies:
        rid = 2
    else:
        rid = request.cookies['_ri']

    menu = await Menu.filter(restaurant_id=int(rid)).order_by('size').filter(visible=True, delivery=True).prefetch_related('product', 'category')
    products_dict = {}

    for i in menu:
        type = i.category.type
        if type not in products_dict:
            products_dict[type] = {
                "type": type,
                "items": [],
                "priority": i.category.priority
            }

        existing_item = next((item for item in products_dict[type]["items"] if item["title"] == i.product.title), None)
        if existing_item:
            # Item with the same title already exists, update parameters
            existing_item["id"].append(i.id)
            existing_item["in_stock"].append(i.in_stock)
            existing_item["bonuses"].append(i.bonuses)
            existing_item["prices"].append(i.price)
            existing_item["sizes"].append(i.size)
            existing_item["units"].append(i.unit)
        else:
            products_dict[type]["items"].append({
                "title": i.product.title,
                "img": i.product.img,
                "description": i.product.description,
                "id": [i.id],
                "in_stock": [i.in_stock],
                "bonuses": [i.bonuses],
                "prices": [i.price],
                "sizes": [i.size],
                "units": [i.unit]
            })
    p=sorted(products_dict.values(), key=lambda x: x["priority"])
    clean = [{k: v for k, v in product.items() if k != "priority"} for product in p]
    return {"products": clean}

