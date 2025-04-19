import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware 
from pymongo import MongoClient
import nest_asyncio
import uvicorn
from threading import Thread
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Form, HTTPException
import bcrypt
import random
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 Chrome/114.0.5735.196 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Version/16.0 Mobile Safari/604.1",
]

PROXIES = []

app = FastAPI()

client = MongoClient("mongodb+srv://username:password@cluster1.1234.mongodb.net/mydatabase?retryWrites=true&w=majority&appName=Cluster1")  # or use Atlas URI
db = client["mydatabase"]
collection = db["user_details"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)


class ProductRequest(BaseModel):
    product_name: str

class UserDetails(BaseModel):
    email: str
    password: str

# def scrape_snapdeal(product_name):
#     search_url = f"https://www.snapdeal.com/search?keyword={product_name.replace(' ', '%20')}"
#     headers = {"User-Agent": "Mozilla/5.0"}
#     response = requests.get(search_url, headers=headers)
#     if response.status_code != 200:
#         return {"error": "Failed to fetch data from Snapdeal"}

#     soup = BeautifulSoup(response.text, "html.parser")
#     product = soup.find("div", class_="product-tuple-description")
#     if product:
#         link = product.find("a")["href"]
#         price = product.find("span", class_="product-price").text.strip()
#         return {"name": product_name, "price": price, "link": link}

#     return {"message": "Product not found on Snapdeal"}

# def scrape_shopclues(product_name):
#     search_url = f"https://www.shopclues.com/search?q={product_name.replace(' ', '+')}"
#     headers = {"User-Agent": "Mozilla/5.0"}
#     response = requests.get(search_url, headers=headers)
#     if response.status_code != 200:
#         return {"error": "Failed to fetch data from Shopclues"}

#     soup = BeautifulSoup(response.text, "html.parser")
#     product = soup.find("div", class_="column col3 search_blocks")
#     if product:
#         link = product.find("a")["href"]
#         price = product.find("span", class_="p_price").text.strip()
#         return {"name": product_name, "price": price, "link": link}

#     return {"message": "Product not found on Shopclues"}

def scrape_snapdeal(product_name, max_price=None):
    search_url = f"https://www.snapdeal.com/search?keyword={product_name.replace(' ', '%20')}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    proxy = {"http": random.choice(PROXIES)} if PROXIES else None
    response = requests.get(search_url, headers=headers, proxies=proxy, timeout=10)

    if response.status_code != 200:
        return {"error": "Failed to fetch data from Snapdeal"}

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="product-tuple-description")

    found_any = False

    for product in products:
        name_tag = product.find("p", class_="product-title")
        price_tag = product.find("span", class_="product-price")
        link_tag = product.find("a")

        if name_tag and price_tag and link_tag:
            name = name_tag.text.strip()
            name_lower = name.lower()
            price_str = price_tag.text.strip()
            price_clean = re.sub(r"[^\d]", "", price_str)

            try:
                price_int = int(price_clean)
            except ValueError:
                continue

            if max_price is None or price_int <= max_price:
                link = link_tag["href"]
                full_link = link if link.startswith("http") else "https://www.snapdeal.com" + link
                return {
                    "name": name,
                    "price": f"Rs. {price_int}",
                    "link": full_link
                }

            found_any = True

    if found_any:
        return {"message": "All found items are above price limit"}
    return {"message": "No matching product found on Snapdeal"}


def scrape_shopclues(product_name, max_price=None):
    search_url = f"https://www.shopclues.com/search?q={product_name.replace(' ', '+')}"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    proxy = {"http": random.choice(PROXIES)} if PROXIES else None
    response = requests.get(search_url, headers=headers, proxies=proxy, timeout=10)
    if response.status_code != 200:
        return {"error": "Failed to fetch data from Shopclues"}

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", class_="column col3 search_blocks")

    for product in products:
        name_tag = product.find("h2")
        price_tag = product.find("span", class_="p_price")
        link_tag = product.find("a")

        if name_tag and price_tag and link_tag:
            name = name_tag.text.strip()
            price_str = price_tag.text.strip().replace("₹", "").replace(",", "").strip()
            try:
                price_int = int(re.search(r'\d+', price_str).group())
            except:
                continue

            if max_price is None or price_int <= max_price:
                return {
                    "name": name,
                    "price": f"₹{price_int}",
                    "link": link_tag["href"] if link_tag["href"].startswith("http") else "https://www.shopclues.com" + link_tag["href"]
                }

    return {"message": "No matching product found on Shopclues"}

@app.post("/compare-prices/")
def compare_prices(request: ProductRequest):
    product_name = request.product_name
    snapdeal_data = scrape_snapdeal(product_name)
    shopclues_data = scrape_shopclues(product_name)

    return {"Snapdeal": snapdeal_data, "Shopclues": shopclues_data}

@app.post("/login/")
def login_user(email: str = Form(...), password: str = Form(...)):
    user = collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    stored_hashed_password = user["password"].encode('utf-8')
    input_password = password.encode('utf-8')
    if bcrypt.checkpw(input_password, stored_hashed_password):
        #return RedirectResponse(url="http://localhost:3000", status_code=200)
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/signup/")
def signup(user: UserDetails):
    if collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_data = {"email": user.email, "password": hashed_password}
    collection.insert_one(user_data)  
    return {"message": "New User registered successfully"}

nest_asyncio.apply()
def run():
    uvicorn.run(app, port=8002)
Thread(target=run).start()
