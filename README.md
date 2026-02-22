# AI Endpoint Assistant – README

## 🚀 Overview
This project is a **local AI demo** that simulates a Gemini-style assistant for **Endpoint Support Teams**.  
It includes:

- Real-time Q&A  
- Local file search (uploaded logs / text files)  
- Simulated Google Drive picker  
- SQLite knowledge base  
- Deep research  
- Chat UI with typing animations  
- Source labeling (DB / file / Drive / deep research)

Everything runs **100% locally**.

---

## 📂 Project Structure

assistant_demo/
│
├── backend/
│   ├── app_db.py
│   ├── db_manager.py
│   ├── create_db.py
│   ├── seed_db.py
│   ├── assistant.db
│   ├── uploads/
│
├── data/
│   ├── sample.txt
│   ├── system_log.txt
│   └── endpoint_health.json
│
├── frontend/
│   ├── index.html
│   └── assets/
│
└── README.md

---

## ⚙️ Backend Setup

cd backend  
python3 -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
python3 create_db.py  
python3 seed_db.py  
python3 app_db.py  

Backend runs at:
http://127.0.0.1:5050

---

## 💻 Frontend Setup

cd frontend  
python3 -m http.server 3000  

Frontend runs at:
http://localhost:3000

---

## 📎 Upload Local Files

Click:

+ → Add photos & files

Uploaded files are saved to:

backend/uploads/

They are searched FIRST before DB or KB.

---

## 📁 Add Google Drive Files (Simulated)

Click:

+ → Add from Google Drive

Files are loaded from /data and become searchable.

---

## 🧠 Deep Research

Click:

+ → Deep research

The assistant combines DB + Drive + uploaded files + health logs.

---

## 🔍 File Search Order

1. Uploaded files (backend/uploads)
2. Google Drive files (data/)
3. Data file fallback (.txt)
4. SQLite knowledge base
5. JSON KB
6. Deep research
7. Fallback response

---

## 🛠 Troubleshooting

### Failed to fetch  
Backend not running or missing CORS.

### Uploaded file not found  
Ensure it appears in backend/uploads/

### Drive attach failing  
Fix data_dir path.

---

## 🏁 Stop Servers
CTRL + C for both backend and frontend.

---

## 🎉 Done!
Your assistant is ready for demo with full endpoint workflow support.
