"""
Automated Integration and Unit Tests for FindIt Portal
"""
import os
import sys
from fastapi.testclient import TestClient

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from app import database

client = TestClient(app)


def test_homepage_and_admin_pages():
    """Verify HTML pages serve with 200 OK."""
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "FindIt" in res_home.text

    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert "Admin Moderation" in res_admin.text


def test_stats_endpoint():
    """Verify metrics counter endpoint returns integer statistics."""
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "lost" in data
    assert "found" in data
    assert "returned" in data
    assert data["total"] >= 1


def test_list_items_and_privacy_masking():
    """Verify listing items does NOT expose raw contact details publicly."""
    res = client.get("/api/items")
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    assert len(items) > 0

    first_item = items[0]
    # Check that contact_info is NOT present in public listing
    assert "contact_info" not in first_item
    # Check that masked contact is provided
    assert "contact_info_masked" in first_item
    assert "***" in first_item["contact_info_masked"]


def test_reveal_contact():
    """Verify that specific contact detail request succeeds and includes privacy notice."""
    res = client.get("/api/items")
    item_id = res.json()["items"][0]["id"]

    contact_res = client.get(f"/api/items/{item_id}/contact")
    assert contact_res.status_code == 200
    contact_data = contact_res.json()
    assert "contact_name" in contact_data
    assert "contact_info" in contact_data
    assert "privacy_notice" in contact_data


def test_report_item_validation_and_creation():
    """Verify form submission validation, optional photo upload, and successful item creation."""
    # 1. Test missing title validation failure (status 400)
    invalid_res = client.post("/api/items", data={
        "title": "",
        "type": "lost",
        "category": "Electronics",
        "description": "Some description",
        "location": "Park bench",
        "date_event": "2026-10-11",
        "contact_name": "Jordan",
        "contact_info": "jordan@example.com"
    }, files={"dummy": ("", b"")})
    assert invalid_res.status_code == 400

    # 2. Test valid creation with an attached photo
    fake_photo_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Minimal JPEG header
    valid_res = client.post("/api/items", data={
        "title": "Blue Hydro Flask Water Bottle",
        "type": "lost",
        "category": "Other",
        "description": "32oz cobalt blue bottle with hiking stickers on one side.",
        "location": "Student Recreation Center, Gym Court 2",
        "date_event": "2026-10-11",
        "contact_name": "Jordan Lee",
        "contact_info": "jordan.lee@example.com"
    }, files={
        "photo": ("bottle.jpg", fake_photo_bytes, "image/jpeg")
    })
    assert valid_res.status_code == 201
    created_id = valid_res.json()["item_id"]
    assert created_id is not None

    # Verify it exists in SQLite database with image_url
    item_check = client.get(f"/api/items/{created_id}")
    assert item_check.status_code == 200
    item_data = item_check.json()
    assert item_data["title"] == "Blue Hydro Flask Water Bottle"
    assert item_data["image_url"] is not None
    assert item_data["image_url"].startswith("/static/uploads/")


def test_search_and_filter():
    """Verify search by keyword and filtering by status."""
    # Search by keyword
    res = client.get("/api/items?search=Hydro")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(i["title"] == "Blue Hydro Flask Water Bottle" for i in items)

    # Filter by type
    res_lost = client.get("/api/items?type=lost")
    assert res_lost.status_code == 200
    for it in res_lost.json()["items"]:
        assert it["type"] == "lost"

    # Clean up Hydro Flask test item
    hydro_items = [i for i in res.json()["items"] if i["title"] == "Blue Hydro Flask Water Bottle"]
    for it in hydro_items:
        client.delete(f"/api/admin/items/{it['id']}", headers={"X-Admin-Passcode": "admin123"})


def test_toggle_returned_status():
    """Verify marking an item as returned and toggling back."""
    # Create a temporary item
    create_res = client.post("/api/items", data={
        "title": "Black Umbrella with Wooden Handle",
        "type": "found",
        "category": "Other",
        "description": "Found near entrance umbrella stand.",
        "location": "Main Entrance Lobby",
        "date_event": "2026-10-11",
        "contact_name": "Front Desk Reception",
        "contact_info": "frontdesk@example.com"
    }, files={"dummy": ("", b"")})
    item_id = create_res.json()["item_id"]

    # Toggle to returned
    toggle_res1 = client.post(f"/api/items/{item_id}/toggle-returned")
    assert toggle_res1.status_code == 200
    assert toggle_res1.json()["item"]["is_returned"] == 1

    # Toggle back to active
    toggle_res2 = client.post(f"/api/items/{item_id}/toggle-returned")
    assert toggle_res2.status_code == 200
    assert toggle_res2.json()["item"]["is_returned"] == 0

    # Clean up test item
    client.delete(f"/api/admin/items/{item_id}", headers={"X-Admin-Passcode": "admin123"})


def test_admin_authentication_and_delete():
    """Verify admin passcode authentication and deletion flow."""
    # Create item to delete
    create_res = client.post("/api/items", data={
        "title": "Spam / Duplicate Test Listing",
        "type": "lost",
        "category": "Other",
        "description": "Test spam listing for deletion verification.",
        "location": "Nowhere",
        "date_event": "2026-10-11",
        "contact_name": "Spammer",
        "contact_info": "spam@example.com"
    }, files={"dummy": ("", b"")})
    item_id = create_res.json()["item_id"]

    # Try admin items with wrong passcode -> 401
    bad_res = client.get("/api/admin/items", headers={"X-Admin-Passcode": "wrong_password"})
    assert bad_res.status_code == 401

    # Try admin items with correct passcode -> 200 with full unmasked contacts
    good_res = client.get("/api/admin/items", headers={"X-Admin-Passcode": "admin123"})
    assert good_res.status_code == 200
    admin_items = good_res.json()["items"]
    assert any(i["id"] == item_id for i in admin_items)
    # Check that unmasked contact_info is available to admin
    target_item = next(i for i in admin_items if i["id"] == item_id)
    assert target_item["contact_info"] == "spam@example.com"

    # Delete listing with admin passcode
    del_res = client.delete(f"/api/admin/items/{item_id}", headers={"X-Admin-Passcode": "admin123"})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify listing is gone
    check_res = client.get(f"/api/items/{item_id}")
    assert check_res.status_code == 404


if __name__ == "__main__":
    print("Running FindIt test suite...")
    test_homepage_and_admin_pages()
    print("[PASS] Homepage and Admin pages serve correctly.")
    test_stats_endpoint()
    print("[PASS] Stats metrics counter endpoint works.")
    test_list_items_and_privacy_masking()
    print("[PASS] Items listing with contact privacy masking works.")
    test_reveal_contact()
    print("[PASS] Reveal contact with privacy notice works.")
    test_report_item_validation_and_creation()
    print("[PASS] Report item validation and creation works.")
    test_search_and_filter()
    print("[PASS] Search and filtering works.")
    test_toggle_returned_status()
    print("[PASS] Toggle returned status works.")
    test_admin_authentication_and_delete()
    print("[PASS] Admin passkey authentication and deletion works.")
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
