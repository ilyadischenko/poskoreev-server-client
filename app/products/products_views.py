from fastapi import HTTPException, APIRouter, Response, Request

from app.products.products_models import Products, Menu, ProductsCategories

products_router = APIRouter(
    prefix="/api/v1/products"
)

@products_router.get('/', tags=['Products'])
async def get_product():

    list = await Menu.all().prefetch_related('product')
    return_list = []
    for i in list:
        return_list.append({
            'id': i.id,
            'title': i.product.title,
            'description': i.product.description,
            'price': i.price,
            'quantity': i.quantity,
            'size': i.size
        })
    print(return_list)

    return return_list


@products_router.post('/addProduct', tags=['Products'])
async def add_product(title: str, description: str):
    return await Products.create(title=title, description=description)


@products_router.post('/addProductType', tags=['Products'])
async def add_product_type(type: str):
    return await ProductsCategories.create(type=type)


@products_router.post('/addMenuItem', tags=['Products'])
async def add_menu_item(product: int, type: int, price: int, size: int, quantity: int):
    return await Menu.create(product_id=product, categories_id=type, price=price, size=size, quantity=quantity)

