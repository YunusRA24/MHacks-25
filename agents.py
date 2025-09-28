import os
import requests

# ----------------- Asi1 API call -----------------
ASI1_API_KEY = "sk_c251d1dd99224cd39c6a0dbc7685d8fe44200dbdf5ba49878629c905ef3fb2df"
ASI1_URL = "https://api.asi1.ai/v1/chat/completions"


def call_asi(system_prompt: str, user_content: str) -> str:
    body = {
        "model": "asi1-extended",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    headers = {
        "Authorization": f"Bearer {ASI1_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(ASI1_URL, headers=headers, json=body, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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
DEFAULT_BUDGET = 20.0  # Example default budget when not specified


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


# Intentionally no link generation — user requested no links in output


def get_products_for_ingredients(ingredients, location_id="01400943", budget=None):
    """
    Fetch products from Kroger. If budget is None, do not enforce a cap.
    If budget is a number, skip items that would push total over budget and mark them as skipped.
    Returns: results, total_cost, skipped_count, budget_enforced(bool)
    """
    token = get_kroger_token()
    if not token:
        return [{"error": "Failed to get Kroger API token"}], 0.0, 0, bool(budget is not None)

    headers = {"Authorization": f"Bearer {token}"}
    results = []
    total_cost = 0.0
    skipped_count = 0
    enforce = budget is not None

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
                if enforce and (total_cost + price) > float(budget):
                    results.append({
                        "ingredient": ingredient,
                        "error": f"Skipping, adding this product exceeds budget (current total: {total_cost})",
                    })
                    skipped_count += 1
                else:
                    results.append({
                        "ingredient": ingredient,
                        "description": product.get("description", "No description"),
                        "price": price,
                        "fulfillment": item_info.get("fulfillment", "No fulfillment info"),
                    })
                    total_cost += price
            else:
                results.append({"ingredient": ingredient, "error": "Product not found"})
        except Exception as e:
            results.append({"ingredient": ingredient, "error": str(e)})

    return results, total_cost, skipped_count, enforce


# ----------------- Processing pipeline for frontend -----------------

def process_user_text(raw_text: str):
    """
    Use ASI to parse freeform user text into:
    - ingredients_needed: Python list of ingredients the user needs to buy
      (exclude items the user says they already have)
    - dietary_restrictions: Python list (if present)
    - budget: either a number in USD, or the string 'unlimited', or None
    Then query Kroger and return a compact response.
    """
    system = (
        "You are a strict parser. Given a user message that may contain a recipe, a list of current pantry/fridge items, "
        "dietary preferences, and potentially a budget statement, extract a Python dict with keys: \n"
        "'ingredients_needed' (list of strings: only new items to buy), \n"
        "'dietary_restrictions' (list of strings), \n"
        "'budget' (a number in USD if specified, or the string 'unlimited' if user says unlimited, otherwise null). \n"
        "Return ONLY the Python dict."
    )
    parsed = call_asi(system, raw_text)

    try:
        data = eval(parsed)
        ingredients_needed = data.get('ingredients_needed', [])
        dietary = data.get('dietary_restrictions', [])
        budget_raw = data.get('budget')

        # Normalize budget
        budget_value = None
        if isinstance(budget_raw, str):
            if 'unlimited' in budget_raw.lower():
                budget_value = None  # unlimited
            else:
                try:
                    budget_value = float(budget_raw)
                except Exception:
                    budget_value = None
        elif isinstance(budget_raw, (int, float)):
            budget_value = float(budget_raw)
        else:
            budget_value = None

        # Optional dietary filter
        if dietary:
            allowed = filter_ingredients_by_diet(ingredients_needed, dietary)
        else:
            allowed = ingredients_needed

        products, total, skipped_count, enforced = get_products_for_ingredients(allowed, budget=budget_value)

        budget_text = "Unlimited" if budget_value is None else f"${budget_value:.2f}"
        skipped_text = f", skipped {skipped_count} item(s) due to budget" if enforced and skipped_count else ""
        summary = f"Found {len(products)} items. Est. total: ${total:.2f}. Budget: {budget_text}{skipped_text}."

        # Build pretty, link-free, structured text output
        lines = []
        lines.append("Ingredients allowed by dietary restrictions:")
        lines.append(str(allowed))
        lines.append("----------")
        lines.append("Dietary restrictions identified:")
        lines.append(str(dietary))
        lines.append("----------")
        lines.append("Kroger Products:")
        for p in products:
            ing = p.get("ingredient", "")
            if p.get("error"):
                lines.append(f"{ing}: {p['error']}")
            else:
                desc = p.get("description", "")
                price = p.get("price")
                price_txt = f"${price:.2f}" if isinstance(price, (int, float)) else "—"
                lines.append(f"{ing}: {desc} ({price_txt})")
        lines.append(f"Total cost: ${total:.2f} (Budget: {budget_text})")
        pretty = "\n".join(lines)

        return {
            "summary": summary,
            "ingredients": allowed,
            "products": products,
            "dietary": dietary,
            "budget": None if budget_value is None else float(budget_value),
            "budget_enforced": enforced,
            "skipped": skipped_count,
            "total": total,
            "pretty": pretty,
        }
    except Exception as e:
        return {"error": f"Failed to parse AI output: {e}", "raw": parsed}


# ----------------- AgentMail helpers -----------------

AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "")
AGENTMAIL_API_URL = os.environ.get("AGENTMAIL_API_URL", "https://api.agentmail.to/send")
AGENTMAIL_FROM = os.environ.get("AGENTMAIL_FROM", "EasyEats@agentmail.to")
AGENTMAIL_TO = os.environ.get("AGENTMAIL_TO", "EasyEats@agentmail.to")


def _build_email_html(result: dict) -> str:
    dietary = ", ".join(result.get("dietary") or []) or "no specific preference"
    budget = result.get("budget")
    budget_text = "Unlimited" if budget is None else f"${budget:.2f}"
    total = result.get("total", 0.0)

    rows = []
    for p in result.get("products", []) or []:
        ing = p.get("ingredient", "")
        price = p.get("price")
        price_txt = f"${price:.2f}" if isinstance(price, (int, float)) else "—"
        desc = p.get("description") or p.get("error", "")
        link = p.get("link") or ""
        link_html = f'<a href="{link}">View</a>' if link else ""
        rows.append(f"<tr><td>{ing}</td><td>{price_txt}</td><td>{desc}</td><td>{link_html}</td></tr>")

    table_html = (
        "<table border=1 cellpadding=6 cellspacing=0 style=\"border-collapse:collapse;font-family:Arial,Helvetica,sans-serif;font-size:14px\">"
        "<thead><tr><th>Ingredient</th><th>Price</th><th>Description / Status</th><th>Link</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )

    html = (
        "<div style=\"font-family:Arial,Helvetica,sans-serif;color:#111\">"
        "<h2>EasyEats — Ingredients & Products</h2>"
        f"<p><strong>Summary:</strong> {result.get('summary','')}</p>"
        f"<p><strong>Dietary:</strong> {dietary} &nbsp; | &nbsp; <strong>Budget:</strong> {budget_text} &nbsp; | &nbsp; <strong>Estimated Total:</strong> ${total:.2f}</p>"
        f"{table_html}"
        f"<p style=\"margin-top:16px\">This ingredients list is <strong>{dietary}</strong>.</p>"
        "</div>"
    )
    return html


def _build_email_text(result: dict) -> str:
    dietary = ", ".join(result.get("dietary") or []) or "no specific preference"
    budget = result.get("budget")
    budget_text = "Unlimited" if budget is None else f"${budget:.2f}"
    total = result.get("total", 0.0)

    lines = [
        "EasyEats — Ingredients & Products",
        f"Summary: {result.get('summary','')}",
        f"Dietary: {dietary} | Budget: {budget_text} | Estimated Total: ${total:.2f}",
        "",
        "Items:",
    ]
    for p in result.get("products", []) or []:
        ing = p.get("ingredient", "")
        price = p.get("price")
        price_txt = f"${price:.2f}" if isinstance(price, (int, float)) else "—"
        desc = p.get("description") or p.get("error", "")
        link = p.get("link") or ""
        lines.append(f"- {ing}: {price_txt} — {desc} {('['+link+']') if link else ''}")
    lines.append("")
    lines.append(f"This ingredients list is {dietary}.")
    return "\n".join(lines)


def send_agentmail_email(result: dict, subject: str = "EasyEats — Your Grocery List", to: str = None):
    """Send a detailed email via AgentMail. Uses env AGENTMAIL_API_KEY and URL."""
    if not AGENTMAIL_API_KEY:
        print("AGENTMAIL_API_KEY not set; skipping email send.")
        return {"sent": False, "reason": "missing_api_key"}

    to_addr = to or AGENTMAIL_TO
    html = _build_email_html(result)
    text = _build_email_text(result)

    try:
        headers = {
            "Authorization": f"Bearer {AGENTMAIL_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "from": AGENTMAIL_FROM,
            "to": to_addr,
            "subject": subject,
            "text": text,
            "html": html,
        }
        resp = requests.post(AGENTMAIL_API_URL, headers=headers, json=payload, timeout=15)
        ok = resp.status_code < 300
        if not ok:
            print("AgentMail send failed:", resp.status_code, resp.text)
        return {"sent": ok, "status": resp.status_code, "body": resp.text if not ok else ""}
    except Exception as e:
        print("AgentMail exception:", e)
        return {"sent": False, "reason": str(e)}


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
    products, total, skipped, enforced = get_products_for_ingredients(allowed_ingredients, budget=DEFAULT_BUDGET)
    print("Kroger Products:")
    for p in products:
        print(p)
    print(f"Total cost: ${total:.2f} (Budget: ${DEFAULT_BUDGET})")