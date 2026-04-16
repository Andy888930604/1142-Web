def find_product(products: list, pid: int) -> dict:
    for p in products:
        if p.get("id") == pid:
            return {"success": True, "data": p}
    return {"success": False, "data": None}

def format_price(price: int) -> str:
    return f"${price:,}"


if __name__ == "__main__":
    products = [
        {"id": 1, "name": "Keyboard", "price": 1200},
        {"id": 2, "name": "Mouse", "price": 800},
        {"id": 3, "name": "Monitor", "price": 4500}
    ]
    
   
    result1 = find_product(products, 1)
 
