import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, List

import httpx
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import get_settings

logging.basicConfig(level=logging.INFO)

ADD_PHOTO, ADD_COST, ADD_SALE, ADD_QTY = range(4)
SCAN_PHOTO, SCAN_PICK, SCAN_QTY = range(4, 7)


@dataclass
class DraftProduct:
    photo_bytes: bytes | None = None
    cost_price: float | None = None
    sale_price: float | None = None
    stock_qty: int | None = None


@dataclass
class ScanDraft:
    photo_bytes: bytes | None = None
    matches: List[dict[str, Any]] = field(default_factory=list)
    selected_product: dict[str, Any] | None = None
    quantity: int = 1


def get_draft(context: ContextTypes.DEFAULT_TYPE) -> DraftProduct:
    if "draft" not in context.user_data:
        context.user_data["draft"] = DraftProduct()
    return context.user_data["draft"]


def get_scan_draft(context: ContextTypes.DEFAULT_TYPE) -> ScanDraft:
    if "scan_draft" not in context.user_data:
        context.user_data["scan_draft"] = ScanDraft()
    return context.user_data["scan_draft"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(
        "\n".join(
            [
                "Zembil Vision is ready.",
                "Use /add to save a new product.",
                "Use /scan to identify an item from a photo and log a sale.",
                "Use /cancel to stop the current flow.",
            ]
        ),
        reply_markup=ReplyKeyboardRemove(),
    )


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("draft", None)
    await update.message.reply_text("Send a product photo to begin onboarding.")
    return ADD_PHOTO


async def capture_add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = get_draft(context)
    draft.photo_bytes = await download_photo_bytes(update)
    await update.message.reply_text("Enter purchase price.")
    return ADD_COST


async def capture_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = parse_float(update.message.text)
    if value is None:
        await update.message.reply_text("Send purchase price as a number, for example 1200.")
        return ADD_COST

    draft = get_draft(context)
    draft.cost_price = value
    await update.message.reply_text("Enter selling price.")
    return ADD_SALE


async def capture_sale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = parse_float(update.message.text)
    if value is None:
        await update.message.reply_text("Send selling price as a number, for example 1500.")
        return ADD_SALE

    draft = get_draft(context)
    draft.sale_price = value
    await update.message.reply_text("Enter quantity.")
    return ADD_QTY


async def capture_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = parse_int(update.message.text)
    if value is None:
        await update.message.reply_text("Send quantity as a whole number, for example 4.")
        return ADD_QTY

    draft = get_draft(context)
    draft.stock_qty = value
    settings = get_settings()

    payload = await post_photo_form(
        url=f"{settings.backend_public_url}{settings.api_prefix}/products/onboard",
        photo_bytes=draft.photo_bytes or b"",
        form_data={
            "cost_price": str(draft.cost_price or 0),
            "sale_price": str(draft.sale_price or 0),
            "stock_qty": str(draft.stock_qty or 0),
        },
    )

    product = payload["product"]
    ai_description = payload["ai_description"]
    await update.message.reply_text(
        "\n".join(
            [
                "Saved product:",
                f"Name: {product['name']}",
                f"Category: {product['category']}",
                f"Stock: {product['stock_qty']}",
                f"Sale price: {product['sale_price']}",
                f"AI note: {ai_description['confidence_note']}",
            ]
        )
    )
    context.user_data.pop("draft", None)
    return ConversationHandler.END


async def scan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("scan_draft", None)
    await update.message.reply_text("Send a photo of the item you just sold.")
    return SCAN_PHOTO


async def capture_scan_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scan_draft = get_scan_draft(context)
    scan_draft.photo_bytes = await download_photo_bytes(update)
    settings = get_settings()

    matches = await post_photo_form(
        url=f"{settings.backend_public_url}{settings.api_prefix}/products/match",
        photo_bytes=scan_draft.photo_bytes or b"",
        form_data={},
    )
    if not matches:
        await update.message.reply_text(
            "I could not find a similar product yet. Try onboarding that item first with /add."
        )
        context.user_data.pop("scan_draft", None)
        return ConversationHandler.END

    scan_draft.matches = matches
    lines = ["Top matches. Reply with 1, 2, or 3 to choose the sold item."]
    for index, match in enumerate(matches, start=1):
        lines.append(
            f"{index}. {match['name']} | {match['category']} | Birr {match['sale_price']} | stock {match['stock_qty']}"
        )
    await update.message.reply_text("\n".join(lines))
    return SCAN_PICK


async def capture_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scan_draft = get_scan_draft(context)
    choice = parse_int(update.message.text)
    if choice is None or choice < 1 or choice > len(scan_draft.matches):
        await update.message.reply_text("Reply with 1, 2, or 3 to choose one of the matches.")
        return SCAN_PICK

    scan_draft.selected_product = scan_draft.matches[choice - 1]
    await update.message.reply_text("Enter quantity sold.")
    return SCAN_QTY


async def capture_scan_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    quantity = parse_int(update.message.text)
    if quantity is None or quantity < 1:
        await update.message.reply_text("Send quantity sold as a whole number, for example 1.")
        return SCAN_QTY

    scan_draft = get_scan_draft(context)
    if not scan_draft.selected_product:
        await update.message.reply_text("No product selected. Start again with /scan.")
        context.user_data.pop("scan_draft", None)
        return ConversationHandler.END

    settings = get_settings()
    selected = scan_draft.selected_product
    sale_payload = {
        "product_id": selected["id"],
        "quantity": quantity,
        "sale_price": selected["sale_price"],
        "cost_price": await fetch_cost_price(settings, selected["id"]),
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.backend_public_url}{settings.api_prefix}/sales",
            json=sale_payload,
        )
        response.raise_for_status()
        payload = response.json()

    sale = payload["sale"]
    await update.message.reply_text(
        "\n".join(
            [
                "Sale logged:",
                f"Item: {selected['name']}",
                f"Quantity: {quantity}",
                f"Profit: Birr {sale['profit']}",
            ]
        )
    )
    context.user_data.pop("scan_draft", None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("Current flow cancelled.")
    return ConversationHandler.END


async def download_photo_bytes(update: Update) -> bytes:
    photo = update.message.photo[-1]
    file = await photo.get_file()
    buffer = BytesIO()
    await file.download_to_memory(out=buffer)
    return buffer.getvalue()


async def post_photo_form(url: str, photo_bytes: bytes, form_data: dict[str, str]) -> Any:
    files = {"image": ("product.jpg", photo_bytes, "image/jpeg")}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, data=form_data, files=files)
        response.raise_for_status()
        return response.json()


async def fetch_cost_price(settings: Any, product_id: str) -> float:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{settings.backend_public_url}{settings.api_prefix}/products/{product_id}"
        )
        response.raise_for_status()
        payload = response.json()
        return float(payload["cost_price"])


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None


def main() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    application = Application.builder().token(settings.telegram_bot_token).build()

    add_conversation = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_PHOTO: [MessageHandler(filters.PHOTO, capture_add_photo)],
            ADD_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_cost)],
            ADD_SALE: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_sale)],
            ADD_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_quantity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    scan_conversation = ConversationHandler(
        entry_points=[CommandHandler("scan", scan_start)],
        states={
            SCAN_PHOTO: [MessageHandler(filters.PHOTO, capture_scan_photo)],
            SCAN_PICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_pick)],
            SCAN_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_scan_quantity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_conversation)
    application.add_handler(scan_conversation)
    application.run_polling()


if __name__ == "__main__":
    main()
