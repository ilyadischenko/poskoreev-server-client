from fastapi import HTTPException, APIRouter, Response, Request

from app.products.models import Products, Menu, ProductsCategories

products_router = APIRouter(
    prefix="/api/v1/products"
)


@products_router.get('/', tags=['Products'])
async def get_product():
    list = await Menu.all().prefetch_related('product').order_by('quantity', '-quantity')
    ord = await Menu.all().prefetch_related('product').values('categories_id')
    print(ord)
    raw = []
    return_list = []
    new = True
    c = -1
    for j, i in enumerate(list):
        raw.append({
            'title': i.product.title,
            'description': i.product.description,
            'price': [i.price],
            'quantity': [i.quantity],
            'size': [i.size],
            'bonuses': [i.bonuses]
        })
        if new:
            return_list.append(raw[j])
            c += 1
        else:
            if raw[j]["title"] == return_list[c]["title"]:
                return_list[c]["price"] = return_list[c]["price"] + raw[j]["price"]
                return_list[c]["quantity"] = return_list[c]["quantity"] + raw[j]["quantity"]
                return_list[c]["size"] = return_list[c]["size"] + raw[j]["size"]
                return_list[c]["bonuses"] = return_list[c]["bonuses"] + raw[j]["bonuses"]
            else:
                return_list.append(raw[j])
                c += 1
        if raw[j]["title"] == return_list[c]["title"]:
            new = False
        else:
            new = True

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
