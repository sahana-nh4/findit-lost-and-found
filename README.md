# FindIt — Community Lost & Found Portal

A complete, beginner-friendly web application designed to connect local communities, campuses, and neighborhoods to report, search, and reunite lost and found items.

---

## 🚀 Tech Stack

- **Frontend:** Responsive Vanilla HTML5, CSS3, Modern JavaScript (Fetch API, zero npm/build dependencies)
- **Backend:** Python 3.12+ with [FastAPI](https://fastapi.tiangolo.com/) and [Uvicorn](https://www.uvicorn.org/)
- **Database:** SQLite (persisted locally in `findit.db`)

---

## 📁 Project Structure & File Purpose

```
FindIt/
├── app/
│   ├── __init__.py           # Package marker for the backend application
│   ├── database.py           # SQLite database connection, table schema, seeding, and queries
│   └── routes.py             # FastAPI REST endpoints (items CRUD, search, contact, admin)
├── static/
│   ├── css/
│   │   └── style.css         # Modern, responsive design system & component styles
│   ├── js/
│   │   ├── app.js            # Homepage frontend logic (search, tabs, modal, reporting)
│   │   └── admin.js          # Admin dashboard frontend logic (passcode auth, deletion)
│   └── uploads/              # Local storage for user-uploaded item photos
├── templates/
│   ├── index.html            # Public homepage with search bar, metrics, tabs, & reporting modal
│   └── admin.html            # Simple administrator moderation dashboard
├── main.py                   # FastAPI application initialization & static file mounting
├── requirements.txt          # Python dependencies
└── README.md                 # Setup, architecture, and usage guide
```

---

## 🔒 Privacy & Security Design

1. **Contact Information Privacy:**
   - In public listings, contact details (phone numbers and email addresses) are **not displayed openly** and are masked (e.g. `a***n@campus.edu`).
   - This prevents automated web scraping, identity harvesting, and spam.
   - To contact the finder or owner, visitors click **"Details & Contact"** and intentionally choose **"Reveal Contact Details"**, accompanied by a community safety reminder to verify proof of ownership.

2. **Honest Authentication Disclaimer:**
   - The administration dashboard (`/admin`) uses a straightforward **local administrator passkey** (default: `admin123`, configurable via the `ADMIN_PASSCODE` environment variable).
   - This is designed for beginner-friendly local moderation demonstrations. It is intentionally simple and not claimed to be enterprise multi-tenant OAuth/JWT authentication.

---

## ⚡ Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

```bash
python --version
```

### 2. Install Dependencies
In your terminal, navigate to the project directory and install the required packages:

```bash
pip install -r requirements.txt
```

*(Packages installed: `fastapi`, `uvicorn`, `python-multipart`)*

### 3. Run the Application
Start the local development server:

```bash
python -m uvicorn main:app --reload --port 8000
```

### 4. Open in Your Browser
- **Public Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Admin Moderation:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) *(Passcode: `admin123`)*
- **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ✨ Features Walkthrough

1. **Dynamic Homepage & Live Metrics:**
   - Displays real-time counts for Total Listings, Active Lost, Active Found, and Reunited items.
   - Initialized with sample community listings on first run for immediate testing.

2. **Instant Search & Multi-criteria Filtering:**
   - Search by item name, description keywords, or location.
   - Filter by status tabs: *All Listings*, *Lost Items*, *Found Items*, and *Reunited / Resolved*.
   - Filter by category dropdown (Electronics, Wallets & Bags, Keys, Pets, Documents, etc.).

3. **Report Lost / Found Items:**
   - Interactive report modal with type toggle (🔴 I Lost Something / 🟢 I Found Something).
   - Validation for item name, category, date, location, description, reporter name, and contact info.
   - Optional photo attachment with instant client-side preview (supports PNG, JPG, JPEG, WEBP up to 5MB).

4. **Mark as Returned / Resolved:**
   - One-click status toggling directly from the card or item details modal.
   - Updates the item badge to "✓ Reunited" and updates the stats counter automatically.

5. **Admin Moderation Dashboard (`/admin`):**
   - Protected by passkey (`admin123`).
   - Displays full unmasked contact details for administrative review.
   - Allows deletion of inappropriate or duplicate listings with instant server cleanup.

---

## 🧪 Testing the Essential Workflows

You can verify all workflows right away:
1. **Browse & Search:** Type "wallet" or "keys" into the search bar to test instant filtering.
2. **Report an Item:** Click **"+ Report Item"**, fill in the details, choose an optional photo, and submit. Check that the new card appears instantly and is saved in SQLite.
3. **Reunite an Item:** Click **"Mark as Reunited"** on an active listing. Notice the badge change and stats update.
4. **View Protected Contact:** Click **"Details & Contact"** on any item, then click **"Reveal Contact Details"** to view the phone/email.
5. **Admin Moderation:** Go to `/admin`, enter `admin123`, filter listings, and test deleting an inappropriate test listing.
