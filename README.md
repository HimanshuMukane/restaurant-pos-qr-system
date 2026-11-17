# Unified Multi-Tenant Restaurant POS & QR Ordering System

A comprehensive, production-ready single-runtime Restaurant POS and QR Code Ordering & Feedback web application built with **Flask (Python)**, **MySQL 8.0**, **Docker Compose**, and **Socket.IO**.

---

## 🚀 Key Features

1. **Unified Single-Runtime Architecture**:
   - Seamlessly unifies all Point-of-Sale (POS) capabilities (billing, live table tracking, takeaway, kitchen ticket generation, reservations, floor layouts, shift reporting) with guest QR capabilities (table QR code scanning, dynamic digital menu, modifier & dish selections, portions, cart, and instant order dispatching).
   - Real-time updates delivered to the POS dashboard via WebSocket / Socket.IO when guests place orders via QR code.

2. **Customer Feedback & Rating System**:
   - Guests can submit structured reviews directly from their table (`/feedback?table=<id>&session=<id>`).
   - Tracks 1-to-5 star overall experience, food quality, service speed, and qualitative comments.
   - Comprehensive JSON feedback API at `/api/feedback`.

3. **Multi-Tenancy via `tenant_id`**:
   - Complete tenant isolation across all models (`sessions`, `order_items`, `payments`, `reservations`, `reservation_items`, `floor_layouts`, `users`, `tenant_feedback`).
   - Dynamic tenant context detection via query parameter (`?tenant=...`), request header (`X-Tenant-ID`), or authenticated session.

4. **Containerized Database & Admin GUI**:
   - Docker Compose configuration for **MySQL 8.0** and **phpMyAdmin**.
   - Auto-initialization scripts and reproducible database dumps included.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+ / Flask 3.x, Flask-Login, Flask-SocketIO, PyMySQL
- **Frontend**: HTML5, Modern CSS, Vanilla JavaScript, Socket.IO Client
- **Database**: MySQL 8.0 (InnoDB, utf8mb4)
- **DevOps**: Docker Compose, phpMyAdmin

---

## 📦 Getting Started

### 1. Launch MySQL and phpMyAdmin
```bash
docker compose up -d
```
- **MySQL Port**: `3306` (`pos_user` / `pos_password`, database: `pos_qr_db`)
- **phpMyAdmin GUI**: [http://localhost:8085](http://localhost:8085)

### 2. Configure Environment
A default `.env.example` is provided:
```bash
cp .env.example .env
```

### 3. Install Dependencies & Run
```bash
pip install -r requirements.txt
python run.py
```
The application will start on `http://localhost:5000`.

---

## 🔐 Default Credentials & Seed Data

### Default Tenants:
- `default`: Main Branch Restaurant
- `branch2`: Downtown Bistro

### Demo Users:
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Cashier | `cashier` | `cashier123` |
| Waiter | `waiter` | `waiter123` |

---

## 🌐 Endpoints

- **POS Dashboard**: `http://localhost:5000/`
- **POS Login**: `http://localhost:5000/login?tenant=default`
- **Customer QR Menu**: `http://localhost:5000/order/<table_number>/<session_id>?tenant=default`
- **Customer Feedback Form**: `http://localhost:5000/feedback?table=<table_number>&session=<session_id>&tenant=default`
- **Feedback JSON API**: `http://localhost:5000/api/feedback?tenant=default`
- **phpMyAdmin**: `http://localhost:8085/`
