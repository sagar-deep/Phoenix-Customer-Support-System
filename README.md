# Phoenix Customer Support System 

A customer support and complaint management system built with **Python (Flask)** and **MySQL**.

---

## Folder Structure

```
phoenix_ai/
├── app.py               ← Flask application (routes, chatbot logic)
├── db.py                ← MySQL connection helper
├── setup.sql            ← Database & sample data
├── requirements.txt
├── templates/
│   ├── index.html       ← Chat UI
│   └── admin.html       ← Admin panel
└── static/
    ├── css/
    │   ├── style.css    ← Main dark theme styles
    │   └── admin.css    ← Admin-specific styles
    └── js/
        ├── chat.js      ← Chat frontend logic
        └── admin.js     ← Admin actions (close, delete)
```

---

## Setup Instructions

### 1. Install Python packages
```bash
pip install -r requirements.txt
```

### 2. Configure MySQL credentials
Open `db.py` and update:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",       # your MySQL username
    "password": "",           # your MySQL password
    "database": "phoenix_ai",
}
```

### 3. Create the database & tables
```bash
mysql -u root -p < setup.sql
```
Or paste `setup.sql` into MySQL Workbench / phpMyAdmin.

### 4. Run the app
```bash
python app.py
```
Open: **http://127.0.0.1:5000**

---

## Features

| Feature | Details |
|---------|---------|
| Chatbot | Keyword-based responses, multi-step complaint flow |
| Complaint System | Auto ticket IDs (ST101…), CRUD via REST API |
| Order Tracking | Accepts order IDs, random/persisted status |
| Admin Panel | View, close, re-open, delete tickets; stats dashboard |
| Export | Download all complaints as CSV |

## Chat Commands

| Command | Action |
|---------|--------|
| `complaint` | Start complaint filing wizard |
| `history` | View last 10 tickets |
| `search ST101` | Look up a specific ticket |
| `close ST101` | Mark ticket as closed |
| `N642DT684` | Track an order by ID |
| `help` | Show command menu |

## REST API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/chat` | Send a chat message |
| POST | `/api/complaint` | File a complaint directly |
| GET | `/api/complaints` | List all complaints (JSON) |
| PUT | `/api/complaint/<id>` | Update complaint status |
| DELETE | `/api/complaint/<id>` | Delete a complaint |
| GET | `/api/export` | Download complaints CSV |

## DBMS Concepts Demonstrated

- **CRUD** — INSERT, SELECT, UPDATE, DELETE on all three tables
- **Relational tables** — users, complaints, orders
- **Query handling** — parameterised queries (SQL injection safe)
- **Real-world use case** — customer support ticketing system
