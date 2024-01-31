from fastapi import HTTPException, APIRouter, Response, Request

from app.products.products_models import Products, Menu, ProductsCategories

products_router = APIRouter()

@products_router.get('/api/v1/products', tags=['Products'])
async def get_product():

    list = await Menu.all().prefetch_related('product')
    raw=[]
    return_list = []
    new=True
    c=-1
    for j,i in enumerate(list):
        raw.append({
            'title': i.product.title,
            'description': i.product.description,
            'price': [i.price],
            'quantity': [i.quantity],
            'size': [i.size]
        })
        if new:
            print("//if new//")
            return_list.append(raw[j])
            c+=1
            print(f"its new so adding {raw[j]}, c={c}")
        else:
            print("//if new else//")
            print(f"j={j}")
            if raw[j]["title"] == return_list[c]["title"]:
                print("//if raw[j]//")
                print(j)
                print(raw[j])
                return_list[c]["price"]=return_list[c]["price"]+raw[j]["price"]
                return_list[c]["quantity"] = return_list[c]["quantity"] + raw[j]["quantity"]
                return_list[c]["size"] = return_list[c]["size"] + raw[j]["size"]
                print(f"merging lists {return_list[c]}")
            else:
                return_list.append(raw[j])
                c += 1
        if raw[j]["title"] == return_list[c]["title"]:
            print("//if raw[j]//")
            print(j)
            print(raw[j])
            print(f"{raw[j]["title"]}=={return_list[c]["title"]} nothing new")
            new=False
        else:
            print("//if raw[j] else//")
            print(f"{raw[j]["title"]}!={return_list[c]["title"]} its new")
            new = True
    print(return_list)

    return return_list


@products_router.post('/api/v1/products/addProduct', tags=['Products'])
async def add_product(title: str, description: str):
    return await Products.create(title=title, description=description)


@products_router.post('/api/v1/products/addProductType', tags=['Products'])
async def add_product_type(type: str):
    return await ProductsCategories.create(type=type)


@products_router.post('/api/v1/products/addMenuItem', tags=['Products'])
async def add_menu_item(product: int, type: int, price: int, size: int, quantity: int):
    return await Menu.create(product_id=product, categories_id=type, price=price, size=size, quantity=quantity)

