import json
from typing import Any

from app.services.llm_client import llm_invoke_structured

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Healthcare", "Education", "Subscriptions",
    "Investments", "Bills & EMI", "Income", "Transfer", "Cash Withdrawal",
    "Refund", "Rent", "Insurance", "Other",
]

CATEGORY_RULES: dict[str, list[str]] = {
    "Food & Dining": ["swiggy", "zomato", "zepto", "blinkit", "dunzo", "restaurant", "cafe", "dining",
                      "hotel", "pizza", "dominos", "mcdonald", "kfc", "starbucks", "barbeque"],
    "Transportation": ["uber", "ola", "rapido", "metro", "fuel", "petrol", "diesel", "indianoil",
                       "bpcl", "hpcl", "flight", "train", "irctc", "bus", "cab", "auto"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho", "tatacliq",
                 "shopping", "retail", "mintra", "lenskart"],
    "Entertainment": ["netflix", "prime video", "hotstar", "jiocinema", "sonyliv", "zee5",
                      "pvr", "inox", "bookmyshow", "movie", "cinema", "theatre"],
    "Subscriptions": ["spotify", "apple music", "youtube premium", "chatgpt", "github",
                      "google drive", "icloud", "dropbox", "notion", "canva"],
    "Bills & Utilities": ["electricity", "water", "gas", "internet", "broadband", "phone",
                          "mobile recharge", "airtel", "jio", "vi", "bsnl", "credit card payment"],
    "Healthcare": ["hospital", "clinic", "doctor", "pharmacy", "medicine", "apollo", "fortis",
                   "medlife", "1mg", "practo", "health", "lab", "diagnostic"],
    "Investments": ["mutual fund", "sip", "stock", "ppf", "nps", "fixed deposit", "rd",
                    "zerodha", "groww", "angel broking", "upstox", "etf", "crypto"],
    "Income": ["salary", "freelance", "interest", "dividend", "refund", "cashback", "credit",
               "received", "payment received"],
    "Transfer": ["transfer", "neft", "rtgs", "imps", "upi transfer", "to self", "own acc"],
    "Bills & EMI": ["emi", "loan", "personal loan", "home loan", "car loan"],
    "Rent": ["rent", "lease", "landlord"],
    "Insurance": ["insurance", "lic", "health insurance", "life insurance", "vehicle insurance"],
    "Cash Withdrawal": ["cash", "withdrawal", "atm", "withdraw"],
    "Refund": ["refund", "reversal", "cashback", "return"],
}


def classify_keyword(merchant: str, description: str) -> str | None:
    text = (merchant + " " + description).lower()
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in text:
                return category
    return None


async def classify_llm(transactions: list[dict]) -> list[dict[str, Any]]:
    tx_batch = []
    for i, tx in enumerate(transactions):
        tx_batch.append({
            "idx": i,
            "merchant": tx.get("merchant", "") or "",
            "description": tx.get("description", "") or "",
            "amount": tx.get("amount", 0),
        })

    system_prompt = (
        "You are a financial transaction categorizer for Indian bank statements. "
        f"Available categories: {', '.join(CATEGORIES)}. "
        "For each transaction, select the most appropriate category. "
        "Return a JSON object with key 'categorizations' as a list of objects "
        "each containing 'idx' (int) and 'category' (string)."
    )

    prompt = json.dumps(tx_batch, indent=2)
    result = await llm_invoke_structured(
        prompt=prompt,
        system_prompt=system_prompt,
        output_schema={
            "title": "BatchCategorization",
            "type": "object",
            "properties": {
                "categorizations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "idx": {"type": "integer"},
                            "category": {"type": "string"},
                        },
                        "required": ["idx", "category"],
                    },
                },
            },
            "required": ["categorizations"],
        },
    )

    categories_list = result.get("categorizations", [])
    cat_map: dict[int, str] = {c["idx"]: c["category"] for c in categories_list}
    output = []
    for i, tx in enumerate(transactions):
        cat_name = cat_map.get(i, "Other")
        if cat_name not in CATEGORIES:
            cat_name = "Other"
        output.append({**tx, "category_name": cat_name})
    return output


async def categorize_batch(transactions: list[dict]) -> list[dict]:
    classified = []
    llm_batch = []
    for tx in transactions:
        cat = classify_keyword(tx.get("merchant", ""), tx.get("description", ""))
        if cat:
            classified.append({**tx, "category_name": cat})
        else:
            llm_batch.append(tx)

    if llm_batch:
        llm_results = await classify_llm(llm_batch)
        classified.extend(llm_results)

    return classified
