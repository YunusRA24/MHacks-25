import requests

# ----------------- Asi1 API call -----------------
ASI1_API_KEY = "sk_c251d1dd99224cd39c6a0dbc7685d8fe44200dbdf5ba49878629c905ef3fb2df"
ASI1_URL = "https://api.asi1.ai/v1/chat/completions"

def filter_ingredients_by_diet(ingredients, dietary_restrictions):
    """
    Ask LLM which ingredients are allowed given the dietary restrictions.
    Returns the filtered list.
    """
    prompt = (
        f"Hi, I would like to check which of the following ingredients are allowed given "
        f"these dietary restrictions: {dietary_restrictions}. "
        f"Ingredients: {ingredients}. "
        "Please return only the ingredients that follow all restrictions in a Python list format."
    )

    body = {
        "model": "asi1-extended",
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {
        "Authorization": f"Bearer {ASI1_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(ASI1_URL, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        # Convert the returned string to a Python list
        allowed_list = eval(response.json()["choices"][0]["message"]["content"])
        return allowed_list
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return []


# ----------------- Kroger API call -----------------
CLIENT_ID = "abdul-bbc8x400"
CLIENT_SECRET = "b2i-2zrxNPoaW6VsTTj8heqAmjj9Dp5238GUN5Eu"
KROGER_TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
KROGER_PRODUCTS_URL = "https://api.kroger.com/v1/products"
BUDGET = 20.0  # Example budget

def get_kroger_token():
    """Get a valid OAuth2 token from Kroger API"""
    try:
        response = requests.post(
            KROGER_TOKEN_URL,
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Error getting Kroger token: {e}")
        return None

def get_products_for_ingredients(ingredients, location_id="01400943", budget=BUDGET):
    """Fetch products from Kroger and respect budget"""
    token = get_kroger_token()
    if not token:
        return [{"error": "Failed to get Kroger API token"}], 0.0

    headers = {"Authorization": f"Bearer {token}"}
    results = []
    total_cost = 0.0

    for ingredient in ingredients:
        try:
            params = {"filter.term": ingredient, "filter.locationId": location_id, "filter.limit": 1}
            response = requests.get(KROGER_PRODUCTS_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("data"):
                product = data["data"][0]
                item_info = product.get("items", [{}])[0] if product.get("items") else {}
                price_str = item_info.get("price", {}).get("regular")
                price = float(price_str) if price_str else 0.0

                if total_cost + price <= budget:
                    results.append({
                        "ingredient": ingredient,
                        "description": product.get("description", "No description"),
                        "price": price,
                        "fulfillment": item_info.get("fulfillment", "No fulfillment info"),
                    })
                    total_cost += price
                else:
                    results.append({
                        "ingredient": ingredient,
                        "error": f"Skipping, adding this product exceeds budget (current total: {total_cost})"
                    })
            else:
                results.append({"ingredient": ingredient, "error": "Product not found"})
        except Exception as e:
            results.append({"ingredient": ingredient, "error": str(e)})

    return results, total_cost


# ----------------- Combined Usage -----------------
if __name__ == "__main__":
    ingredients = ["hummus", "spinach", "chicken", "almonds"]
    dietary_restrictions = ["vegan", "gluten-free"]

    # Step 1: Filter ingredients by dietary restrictions
    allowed_ingredients = filter_ingredients_by_diet(ingredients, dietary_restrictions)
    print("Ingredients allowed by dietary restrictions:")
    print(allowed_ingredients)
    print("----------")

    # Step 2: Fetch products for allowed ingredients
    products, total = get_products_for_ingredients(allowed_ingredients)
    print("Kroger Products:")
    for p in products:
        print(p)
    print(f"Total cost: ${total:.2f} (Budget: ${BUDGET})")