<div align="center">

# 🔐 TrustShare

### Secure. Intelligent. Transparent.

**A modern full-stack secure file-sharing platform built to protect your files, monitor access, and give you complete control over your data.**

<p>
  <img src="https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Python-Backend-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Status-In%20Development-orange?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square"/>
</p>

</div>

---

## 🧭 What is TrustShare?

**TrustShare** is a secure file-sharing system designed around one simple idea:

> **Sharing a file shouldn't mean losing control of it.**

Traditional file-sharing platforms often focus primarily on uploading and downloading files. TrustShare goes further by combining **secure file management, controlled sharing, access monitoring, auditability, and intelligent search** into a unified platform.

Whether you're storing an important document, sharing a project file with a teammate, or investigating unusual access activity, TrustShare provides visibility into **what happened, when it happened, and who accessed your data.**

---

## ✨ Core Features

### 📁 Smart File Management

Manage your files through a centralized workspace.

* Upload and organize files
* Folder-based organization
* File categorization
* File metadata management
* Secure file access
* Download management
* Trash and restore functionality
* Permanent file deletion

---

### 🔗 Secure File Sharing

Share files without giving away unnecessary control.

* Controlled file sharing
* Shared-file management
* Access-aware sharing
* Permission-based access
* Share history
* Secure access workflows

---

### 🛡️ Access Monitoring

TrustShare provides visibility into how your files are being used.

```text
             ┌─────────────────────┐
             │      TRUSTSHARE      │
             └──────────┬──────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     File Access    Downloads     Login Activity
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                 ┌──────────────┐
                 │  Audit Logs  │
                 └──────┬───────┘
                        ▼
              Security Monitoring
```

The monitoring layer is designed to provide:

* 📥 Download tracking
* 📂 File access history
* 🔑 Login activity monitoring
* 📜 Audit logs
* 🚨 Security event monitoring
* 🔍 Suspicious activity detection

---

### 🤖 AI-Powered Content Search

Finding a document shouldn't require remembering its exact filename.

TrustShare includes an AI-powered semantic search architecture that can understand document content and retrieve relevant files based on **meaning**, rather than only exact keywords.

The search pipeline can be represented as:

```text
Document
   │
   ▼
Text Extraction
   │
   ▼
Document Chunking
   │
   ▼
Embedding Model
   │
   ▼
Vector Representation
   │
   ▼
Qdrant Vector Database
   │
   ▼
Semantic Search
   │
   ▼
Relevant Documents
```

The system is designed around technologies such as:

* Sentence Transformers
* Vector embeddings
* Qdrant
* Semantic document retrieval

---

## 🏗️ Architecture

TrustShare follows a modular full-stack architecture.

```text
                         ┌──────────────────────┐
                         │       CLIENT         │
                         │      React App       │
                         └──────────┬───────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌──────────────────────┐
                         │       SERVER         │
                         │       FastAPI        │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ PostgreSQL  │       │   Storage   │       │   Qdrant    │
       │  Database   │       │    Layer    │       │ Vector DB   │
       └─────────────┘       └─────────────┘       └─────────────┘
                                    │
                                    ▼
                           Document Processing
                                    │
                                    ▼
                              AI Search Layer
```

---

## 🖥️ Frontend

The frontend is built with **React** and follows a feature-oriented structure.

```text
client/
│
├── src/
│   ├── pages/
│   │   └── Dashboard.js
│   │
│   ├── features/
│   │   └── dashboard/
│   │       ├── components/
│   │       ├── hooks/
│   │       └── services/
│   │
│   └── ...
│
└── package.json
```

The frontend is responsible for:

* User interface
* Navigation
* Dashboard
* File management
* Sharing workflows
* Monitoring views
* Authentication flows
* API communication

---

## ⚙️ Backend

The backend is powered by **FastAPI** and organized into modular application domains.

```text
server/
│
├── src/
│   ├── dashboard/
│   │   ├── controller
│   │   ├── models
│   │   └── database service
│   │
│   ├── ...
│   │
│   └── main.py
│
├── .env.example
├── docker-compose.yml
└── ...
```

FastAPI provides the API layer between the frontend, database, file system, and intelligent search services.

---

# 🗄️ Database

TrustShare uses **PostgreSQL** as its primary database.

The application uses:

* PostgreSQL 16
* SQLAlchemy
* psycopg2

PostgreSQL stores application data such as:

```text
Users
  │
  ├── Files
  │     ├── Categories
  │     ├── Folders
  │     └── Metadata
  │
  ├── Shared Files
  │
  ├── Access Records
  │
  └── Security Events
```

SQLite is reserved for isolated unit-test scenarios.

---

# 🐳 Docker Development Environment

TrustShare includes a Docker-based development environment.

The Compose stack provides:

```text
┌───────────────────────────────┐
│        Docker Compose         │
│                               │
│  ┌─────────────┐              │
│  │ PostgreSQL  │              │
│  │     16      │              │
│  └──────┬──────┘              │
│         │                     │
│         │ Health Check        │
│         ▼                     │
│  ┌─────────────┐              │
│  │   FastAPI   │              │
│  │   Backend   │              │
│  └─────────────┘              │
│                               │
└───────────────────────────────┘
```

Start the development environment:

```powershell
cd project-root/server

Copy-Item .env.example .env

docker compose up --build
```

> **Important:** Never commit production credentials, database passwords, JWT secrets, API keys, or `.env` files to source control.

---

# 🚀 Getting Started

## 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/TrustShare.git
cd TrustShare
```

---

## 2️⃣ Start the Backend

```powershell
cd server
python -m src.main
```

The FastAPI application will start locally.

---

## 3️⃣ Start the Frontend

Open another terminal:

```powershell
cd client
npm install
npm start
```

The React development server will start.

---

# 🔐 Environment Variables

Create your environment file from the provided template:

```powershell
Copy-Item .env.example .env
```

Configure your local development values in `.env`.

Example:

```env
POSTGRES_DB=trustshare
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

DATABASE_URL=your_database_connection
```

### ⚠️ Never commit `.env`

Your `.gitignore` should contain:

```gitignore
.env
.env.*
!.env.example
```

---

# 📡 API

The backend exposes RESTful endpoints for different application modules.

Example dashboard endpoint:

```http
GET /api/dashboard/
```

The endpoint requires an authenticated request and returns the dashboard data associated with the current user.

Example API structure:

```text
/api
│
├── /auth
│
├── /dashboard
│
├── /files
│
├── /folders
│
├── /shared
│
├── /monitoring
│
├── /trash
│
└── /search
```

---

# 🗑️ Trash & Recovery

TrustShare provides a recovery-oriented file deletion workflow.

Instead of immediately destroying a deleted file:

```text
Delete File
    │
    ▼
   Trash
    │
    ├───────────────┐
    ▼               ▼
 Restore       Permanent Delete
    │
    ▼
 Original Location
```

This reduces accidental data loss while still allowing users to permanently remove files when required.

---

# 🔎 Project Structure

```text
project-root/
│
├── client/                 # React frontend
│   ├── src/
│   │   ├── pages/
│   │   ├── features/
│   │   └── ...
│   └── package.json
│
├── server/                 # FastAPI backend
│   ├── src/
│   │   ├── dashboard/
│   │   ├── ...
│   │   └── main.py
│   ├── .env.example
│   └── docker-compose.yml
│
├── docs/                   # Project documentation
│
├── .gitignore
├── LICENSE
└── README.md
```

---

# 🧩 Design Philosophy

TrustShare is built around four principles:

### 🔒 Security

Files should remain protected throughout their lifecycle.

### 👁️ Transparency

Users should be able to understand how their files are being accessed.

### ⚡ Simplicity

Security shouldn't make everyday file management unnecessarily complicated.

### 🧠 Intelligence

Modern search and monitoring should help users find information and identify meaningful activity faster.

---

# 🛣️ Roadmap

* [x] React frontend foundation
* [x] FastAPI backend foundation
* [x] PostgreSQL integration
* [x] Dashboard architecture
* [x] File management
* [x] Trash and recovery
* [x] Shared-file architecture
* [x] Access monitoring architecture
* [x] Audit logging architecture
* [x] Advanced suspicious-activity detection
* [x] Enhanced semantic search
* [x] Role-based access improvements
* [x] Advanced security analytics
* [x] Production deployment
* [x] Automated testing and CI/CD

---

# 🧪 Development

Run backend:

```bash
cd server
python -m src.main
```

Run frontend:

```bash
cd client
npm start
```

Run PostgreSQL + backend using Docker:

```bash
cd server
docker compose up --build
```

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

### Development workflow

```bash
git checkout -b feature/your-feature
```

Make your changes, test them, and commit:

```bash
git add .
git commit -m "feat: add your feature"
```

Push your branch:

```bash
git push origin feature/your-feature
```

Then open a Pull Request.

---

# 📜 License

This project is licensed under the **MIT License**.

See [`LICENSE`](LICENSE) for more information.

---

<div align="center">

## 🔐 TrustShare

### **Your files. Your access. Your trust.**

Built with ❤️ using React, FastAPI, PostgreSQL, Docker, and modern AI technologies.

⭐ **If you find this project useful, consider giving it a star.**

</div>
