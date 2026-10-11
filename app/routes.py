import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, status
from pydantic import BaseModel, Field

from app import database

router = APIRouter(prefix="/api")

ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "admin123")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class AdminVerifyRequest(BaseModel):
    passcode: str


@router.get("/stats")
def get_stats():
    """Returns portal count metrics for lost, found, and reunited items."""
    return database.get_portal_stats()


@router.get("/items")
def list_items(
    search: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Retrieves lost and found items.
    Contact information is masked by default for privacy to prevent automated scraping.
    """
    items = database.get_all_items(
        search=search,
        item_type=type,
        category=category,
        status_filter=status,
        reveal_contacts=False
    )
    return {"items": items, "count": len(items)}


@router.get("/items/{item_id}")
def get_item_details(item_id: int):
    """Retrieves a single item's details."""
    item = database.get_item_by_id(item_id, reveal_contacts=False)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/items/{item_id}/contact")
def get_item_contact(item_id: int):
    """
    Endpoint to view full contact details when a user wants to contact the finder/owner.
    Protected behind intentional request with privacy advisory.
    """
    item = database.get_item_by_id(item_id, reveal_contacts=True)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": item["id"],
        "title": item["title"],
        "contact_name": item["contact_name"],
        "contact_info": item["contact_info"],
        "privacy_notice": "Contact details are provided solely to facilitate safe item returns. Verify proof of ownership before meeting."
    }


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def report_item(
    title: str = Form(""),
    type: str = Form(""),
    category: str = Form(""),
    description: str = Form(""),
    location: str = Form(""),
    date_event: str = Form(""),
    contact_name: str = Form(""),
    contact_info: str = Form(""),
    photo: Optional[UploadFile] = None
):
    """
    Submits a new lost or found item report with optional photo upload and field validations.
    """
    # 1. Basic validation
    title = title.strip()
    if not title or len(title) > 120:
        raise HTTPException(status_code=400, detail="Title is required and must be under 120 characters.")

    item_type = type.strip().lower()
    if item_type not in ["lost", "found"]:
        raise HTTPException(status_code=400, detail="Item type must be either 'lost' or 'found'.")

    category = category.strip()
    if not category:
        raise HTTPException(status_code=400, detail="Category is required.")

    description = description.strip()
    if not description or len(description) > 2000:
        raise HTTPException(status_code=400, detail="Description is required and must be under 2000 characters.")

    location = location.strip()
    if not location or len(location) > 150:
        raise HTTPException(status_code=400, detail="Location is required and must be under 150 characters.")

    date_event = date_event.strip()
    if not date_event:
        raise HTTPException(status_code=400, detail="Date is required (YYYY-MM-DD).")

    contact_name = contact_name.strip()
    if not contact_name or len(contact_name) > 80:
        raise HTTPException(status_code=400, detail="Contact person name is required.")

    contact_info = contact_info.strip()
    if not contact_info or len(contact_info) > 100:
        raise HTTPException(status_code=400, detail="Contact email or phone number is required.")

    # 2. Handle optional photo upload
    image_url = None
    if photo and photo.filename:
        filename = photo.filename
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Ensure upload folder exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Unique safe filename
        safe_filename = f"{uuid.uuid4().hex[:12]}_{date_event}{ext}"
        target_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Read content and enforce size limit
        file_bytes = await photo.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Uploaded image exceeds 5MB limit.")

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        image_url = f"/static/uploads/{safe_filename}"

    # 3. Save into SQLite
    new_id = database.create_item(
        title=title,
        item_type=item_type,
        category=category,
        description=description,
        location=location,
        date_event=date_event,
        contact_name=contact_name,
        contact_info=contact_info,
        image_url=image_url
    )

    return {
        "success": True,
        "message": f"Successfully reported {item_type} item: {title}",
        "item_id": new_id
    }


@router.post("/items/{item_id}/toggle-returned")
def toggle_returned(item_id: int):
    """
    Marks an item as returned/resolved, or toggles back to active.
    """
    updated = database.toggle_returned_status(item_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")

    status_str = "Returned / Resolved" if updated["is_returned"] == 1 else "Active"
    return {
        "success": True,
        "message": f"Item '{updated['title']}' updated to {status_str}.",
        "item": updated
    }


# ==================== ADMIN ENDPOINTS ====================
def verify_admin(x_admin_passcode: Optional[str] = Header(None)):
    """Verifies the simple admin passcode."""
    if not x_admin_passcode or x_admin_passcode != ADMIN_PASSCODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access denied. Invalid or missing passcode (default is 'admin123')."
        )


@router.post("/admin/verify")
def check_admin_passcode(payload: AdminVerifyRequest):
    """Validates the admin passcode for frontend login check."""
    if payload.passcode == ADMIN_PASSCODE:
        return {"valid": True, "message": "Admin authorized"}
    raise HTTPException(status_code=401, detail="Incorrect admin passcode.")


@router.get("/admin/items")
def admin_list_items(
    search: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    x_admin_passcode: Optional[str] = Header(None)
):
    """Admin endpoint: lists all items with full unmasked contact details."""
    verify_admin(x_admin_passcode)
    items = database.get_all_items(
        search=search,
        item_type=type,
        category=category,
        status_filter=status,
        reveal_contacts=True
    )
    return {"items": items, "count": len(items)}


@router.delete("/admin/items/{item_id}")
def admin_delete_item(item_id: int, x_admin_passcode: Optional[str] = Header(None)):
    """Admin endpoint: deletes an inappropriate or duplicate listing."""
    verify_admin(x_admin_passcode)
    # Check if item exists to optionally clean up uploaded photo
    item = database.get_item_by_id(item_id, reveal_contacts=True)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.get("image_url") and item["image_url"].startswith("/static/uploads/"):
        filename = os.path.basename(item["image_url"])
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

    success = database.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete item")

    return {
        "success": True,
        "message": f"Listing #{item_id} ('{item['title']}') was deleted successfully."
    }
