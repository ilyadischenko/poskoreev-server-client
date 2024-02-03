from fastapi import HTTPException, APIRouter, Response, Request

from app.products.models import Product, Menu, ProductCategory

products_router = APIRouter(
    prefix="/api/v1/products"
)


@products_router.get('/', tags=['Products'])
async def get_product():
    menu = await Menu.all().prefetch_related('product').order_by('size')
    products=[]
    c=0
    for i in menu:
        products.append({"type": i.category_id,
                         "items": {
                             "id": i.id,
                             "title": i.product.title,
                             "img": i.product.img,
                             "description": i.product.description,
                             "in_stock": i.in_stock,
                             "visible": i.visible
                         }})
        products[c]["items"].update(bonuses=[i.bonuses for i in menu if i.product.title==products[c]["items"]["title"]],
                                    prices=[i.price for i in menu if i.product.title==products[c]["items"]["title"]],
                                    sizes=[i.size for i in menu if i.product.title==products[c]["items"]["title"]])
        break
    print([products[i]["items"]["title"] for i in range(len(products))])
    for i in menu:
        if c==0:
            c+=1
            continue
        if [products[i]["items"]["title"] for i in range(len(products))].count(i.product.title):
            continue
        products.append({"type": i.category_id,
                         "items": {
                             "id": i.id,
                             "title": i.product.title,
                             "img": i.product.img,
                             "description": i.product.description,
                             "in_stock": i.in_stock,
                             "visible": i.visible
                         }})
        products[c]["items"].update(bonuses=[i.bonuses for i in menu if i.product.title==products[c]["items"]["title"]],
                                    prices=[i.price for i in menu if i.product.title==products[c]["items"]["title"]],
                                    sizes=[i.size for i in menu if i.product.title==products[c]["items"]["title"]])
        c+=1
    return {"products" : products}


@products_router.post('/addProduct', tags=['Products'])
async def add_product(title: str, description: str):
    return await Product.create(title=title, description=description)


@products_router.post('/addProductType', tags=['Products'])
async def add_product_type(type: str):
    return await ProductCategory.create(type=type)


@products_router.post('/addMenuItem', tags=['Products'])
async def add_menu_item(product: int, type: int, price: int, size: int, quantity: int):
    return await Menu.create(product_id=product, category_id=type, price=price, size=size, quantity=quantity)
