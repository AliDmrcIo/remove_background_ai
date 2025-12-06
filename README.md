# AI Background Remover (End-to-End Full Stack MLOps Project)

🔗 **Live on:** [http://removedbackground.duckdns.org](http://removedbackground.duckdns.org)
This is the live production version of the project. You can directly upload your images and test the AI-based background removal system from this link.



https://github.com/user-attachments/assets/6083e043-fd01-4880-9e18-e37b568b7a19



---

## Project Description

This project is a full-stack, production-ready **AI-powered background removal system**. Users can authenticate with their Google accounts, upload images, remove image backgrounds using a state-of-the-art **semantic segmentation deep learning model**, and manage their processed image history through a secure cloud-based system.

The project is designed as a complete **End-to-End MLOps application**, covering:

* Model serving
* Secure authentication
* Database integration
* Frontend-backend communication
* Containerization
* Cloud deployment

---

## Project Goal

The main goal of this project is to build a **robust, scalable, and secure AI application** that automatically removes image backgrounds using **semantic segmentation**. The focus is not only on machine learning performance but also on:

* Production-level system design
* Secure authentication
* Cloud infrastructure
* Real-world deployment practices
* Full MLOps lifecycle implementation

---

## 🛠️ Technologies Used

### AI & Computer Vision

* **Task:** Semantic Segmentation (Foreground–Background Separation)
* **Model Architecture:** `DeepLabV3+` (Latest generation segmentation architecture)
* **Backbone:** `MobileNetV3-Large` (Optimized for lightweight and CPU-based inference)
* **Frameworks & Libraries:** `PyTorch`, `Torchvision`, `Albumentations`, `OpenCV`

### Backend (API & Business Logic)

* **Framework:** `FastAPI`
* **Authentication:** `Google OAuth 2.0`
* **Authorization & Security:** `JWT` (JSON Web Token)
* **Session Handling:** Secure HTTP-only Cookies
* **Database:** `SQLite`
* **ORM:** `SQLAlchemy`

### Frontend (User Interface)

* **Framework:** `Streamlit`
* **State & Cookie Management:** `extra-streamlit-components`

### DevOps, Container & Cloud

* **Containerization:** `Docker`, `Docker Compose`
* **Cloud Provider:** `AWS EC2` (Ubuntu)
* **Dynamic DNS:** `DuckDNS`
* **Network Routing:** `iptables` Port Forwarding
* **Authentication Flow:** Google Login + Token-Based Access Control

---

## 📂 Project Structure

* **`ai/`**
  * `main.py` → FastAPI application entry point
  * Deep learning model loader
  * Image preprocessing & inference pipeline
* **`backend/`**
  * `auth.py` → Google OAuth, JWT generation & validation
  * `picture_operations.py` → Image upload, processing & history endpoints
* **`frontend/`**
  * `login_page.py` → Google authentication interface
  * `history_page.py` → Displays past user operations
  * `remove_background_page.py` → Image upload & background removal interface
  * `history_detail_page.py` → Shows details of a selected generation
* **`db/`**
  * `database.py` → Database connection
  * `tables.py` → User & image metadata models
* **`Dockerfile`**

  * Optimized CPU-based PyTorch environment for production
* **`docker-compose.yml`**

  * Orchestration of Backend & Frontend containers
* **`.env`**

  * Environment variables (not pushed to GitHub)

---

## How to Run Locally

You can run the system in **two different ways**:

* Using **Docker** (recommended)
* Running services manually without Docker

---

## 1. Environment Variable Configuration (.env)

Create a file named `.env` in the project root directory and configure it exactly like this:

```ini
# --- Google OAuth Configuration ---
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# --- Security ---
SECRET_KEY=your_random_secret_string
JWT_SECRET_KEY=your_random_jwt_secret_string

# --- Redirect Configuration ---
REDIRECT_URL=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:8501
```

Without these variables:

* Google Login will NOT work
* Token security will break
* Backend authentication will fail

---

## 2. Option A: Run with Docker (Recommended)

This is the **fastest and cleanest** way to run the project.

### Requirements

* Docker Desktop installed and running

### Steps

```bash
docker-compose up --build
```

When you see:

```
Application startup complete
```

Open your browser:

```
http://localhost:8501
```

Backend will automatically run on:

```
http://localhost:8000
```

Everything (backend, frontend, AI model, database) runs inside containers.

---

## 3. Option B: Run Without Docker (Manual Setup)

You will need **two separate terminals**.

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Terminal 1 – Start Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend runs at:

```
http://localhost:8000
```

---

### Terminal 2 – Start Frontend

```bash
streamlit run frontend/remove_background_page.py
```

Frontend runs at:

```
http://localhost:8501
```

---

## Authentication Flow

1. User logs in via Google OAuth
2. Backend generates a JWT token
3. Token is stored in secure HTTP-only cookies
4. All protected endpoints require valid JWT
5. User history is stored in SQLite

---

## Production Deployment

* Deployed on `AWS EC2 (Ubuntu)`
* Served via `DuckDNS`
* Traffic routed through `iptables`
* Docker containers run backend and frontend as isolated services

---

## Summary

This project is not just a background remover.
It is a **complete full-stack, cloud-deployed, authenticated, AI-powered MLOps system** that demonstrates:

* Deep Learning in production
* Secure Authentication
* Containerization
* Cloud Networking
* Real-world deployment patterns
