from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category

DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "type": "expense", "keywords": ["swiggy", "zomato", "restaurant", "dining", "cafe"]},
    {"name": "Transportation", "type": "expense", "keywords": ["uber", "ola", "metro", "fuel", "petrol", "bus"]},
    {"name": "Shopping", "type": "expense", "keywords": ["amazon", "flipkart", "myntra", "shopping", "retail"]},
    {"name": "Bills & Utilities", "type": "expense", "keywords": ["electricity", "water", "internet", "recharge", "bill"]},
    {"name": "Entertainment", "type": "expense", "keywords": ["netflix", "prime", "hotstar", "movie", "pvr", "cinema"]},
    {"name": "Healthcare", "type": "expense", "keywords": ["hospital", "doctor", "pharmacy", "medicine", "clinic"]},
    {"name": "Education", "type": "expense", "keywords": ["tuition", "course", "book", "exam", "college"]},
    {"name": "Subscriptions", "type": "expense", "keywords": ["spotify", "youtube", "chatgpt", "github", "subscription"]},
    {"name": "Investments", "type": "investment", "keywords": ["sip", "mutual fund", "stock", "ppf", "nps", "zerodha"]},
    {"name": "Bills & EMI", "type": "expense", "keywords": ["emi", "loan", "personal loan", "home loan"]},
    {"name": "Income", "type": "income", "keywords": ["salary", "freelance", "interest", "dividend", "refund"]},
    {"name": "Transfer", "type": "transfer", "keywords": ["neft", "rtgs", "imps", "upi", "transfer"]},
    {"name": "Rent", "type": "expense", "keywords": ["rent", "lease", "landlord"]},
    {"name": "Insurance", "type": "expense", "keywords": ["insurance", "lic", "health insurance"]},
    {"name": "Cash Withdrawal", "type": "expense", "keywords": ["cash", "withdrawal", "atm"]},
    {"name": "Refund", "type": "income", "keywords": ["refund", "reversal", "cashback", "return"]},
    {"name": "Other", "type": "expense", "keywords": []},
]


async def seed_default_categories(db: AsyncSession):
    for cat_data in DEFAULT_CATEGORIES:
        result = await db.execute(
            select(Category).where(Category.name == cat_data["name"], Category.is_default == True)
        )
        existing = result.scalar_one_or_none()
        if not existing:
            cat = Category(
                name=cat_data["name"],
                type=cat_data["type"],
                is_default=True,
                keywords=cat_data["keywords"],
            )
            db.add(cat)
    await db.commit()
