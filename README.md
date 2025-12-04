Library Management System

A modern, distributed library management application built using Django, gRPC, and Python.
This project demonstrates a clean client–server architecture designed for scalable library operations such as book management, user authentication, borrowing workflows, and administrative tasks.

Features
Authentication & User Management

Secure login system using Django authentication

Role-based access: Librarian, Admin

Superuser account for full system control

Book & Library Operations

Add, edit, delete books

Borrow and return operations

Real-time status updates via gRPC

Book availability and history tracking

Client–Server Architecture

Server: Django + gRPC backend handling business logic

Client: Frontend interface communicating with the server through gRPC

Ensures fast, reliable, and structured communication

Database Support

MySQL integration for persistent storage

Fully managed by Django ORM and migrations

Project Structure
LibraryManagementSystem/
│
├── Client/                   # Frontend interface (Python + gRPC)
│   ├── library_admin/
│   ├── library_pb2.py        # Generated protobuf classes
│   ├── library_pb2_grpc.py   # gRPC stubs
│   └── manage.py
│
├── server/                   # Django + gRPC backend
│   ├── library_server/
│   ├── grpc_handler.py       # gRPC server implementation
│   ├── library.proto         # Protocol Buffers schema
│   └── manage.py
│
├── requirements.txt          # Python dependencies
└── README.md

Technologies Used
Technology	Purpose
Django	Web framework + authentication system
gRPC	High-performance communication between client and server
Protocol Buffers	Strict, typed communication schema
MySQL	Main database for library records
Python 3.x	Core programming language
