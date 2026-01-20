# 📚 Library Management System

A modern, distributed library management application built with **Django**, **gRPC**, and **Python**.

This project demonstrates a clean **client–server architecture** designed to support scalable library operations such as book management, user authentication, borrowing workflows, and administrative tasks.

---

## 🚀 Features

### 🔐 Authentication & User Management
- Secure login system powered by Django.
- Role-based access: **Librarian**, **Admin**.
- Superuser account with full system control.

### 📘 Book & Library Operations
- Add, edit, and delete books.
- Borrow and return workflows.
- Real-time status updates via gRPC.
- Tracking of book availability and history.

### 🖧 Client–Server Architecture
- **Server:** Django + gRPC backend handling core logic.
- **Client:** Frontend application communicating through gRPC.
- Ensures fast, reliable, and structured communication between components.

### 🗄️ Database Support
- Integrated **MySQL** database for persistent data storage.
- Fully managed via Django ORM and migrations.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Django** | Web framework & authentication system |
| **gRPC** | High-performance communication layer |
| **Protocol Buffers** | Typed communication schema |
| **MySQL** | Main database for library records |
| **Python 3.x** | Core programming language |

---

## 📁 Project Structure

