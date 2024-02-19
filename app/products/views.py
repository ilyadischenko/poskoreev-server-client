from fastapi import HTTPException, APIRouter, Response, Request

from app.products.models import Product, Menu, ProductCategory

products_router = APIRouter(
    prefix="/api/v1/products"
)


@products_router.get('/', tags=['Products'])
async def get_product(request: Request):
    rid = request.cookies['_ri']
    if not rid: raise HTTPException(status_code=400, detail="PLEASE pick restaurant")
    menu = await Menu.filter(restaurant_id=int(rid)).order_by('size').filter(visible=True).prefetch_related('product', 'category')
    products_dict = {}

    for i in menu:
        type = i.category.type
        if type not in products_dict:
            products_dict[type] = {
                "type": type,
                "items": []
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
            # Create a new item
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
    # Convert dictionary values to a list
    p=dict(sorted(products_dict.items()))
    products = list(p.values())
    return {"products": products}


@products_router.post('/addProduct', tags=['Products'])
async def add_product(title: str, description: str):
    return await Product.create(title=title, description=description)


@products_router.post('/addProductType', tags=['Products'])
async def add_product_type(type: str):
    return await ProductCategory.create(type=type)


@products_router.post('/addMenuItem', tags=['Products'])
async def add_menu_item(restaurant_id: int, product: int, type: int, price: int, size: int, unit: str):
    return await Menu.create(restaurant_id=restaurant_id, product_id=product, category_id=type, price=price, size=size, unit=unit)
