# In Client/client_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from django.core.files.storage import FileSystemStorage # NEW: For file handling
from .grpc_client import LibraryClient

# ----------------------------------------------------
# A. Authentication Views (No Change)
# ----------------------------------------------------

def staff_login(request: HttpRequest):
    # If already logged in
    if request.session.get('staff_id'):
        return redirect('dashboard')

    message = request.session.pop('login_message', None)

    # 🔹 Add your media images here
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        client = LibraryClient()
        auth_response = client.staff_login(username, password)

        if auth_response.success:
            request.session['staff_id'] = auth_response.user_id
            request.session['username'] = username
            return redirect('dashboard')
        else:
            message = auth_response.message

    context = {
        'message': message,
        'bg_image': bg_image,
        'logo_image': logo_image,
    }
    return render(request, 'client_app/login.html', context)


def staff_logout(request: HttpRequest):
    request.session.clear()
    request.session['login_message'] = "You have been logged out."
    return redirect('staff_login')


# ----------------------------------------------------
# B. Core Management Views 
# ----------------------------------------------------

def dashboard(request: HttpRequest):
    # 🔹 Add your media images here
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"
    # ... (Implementation remains the same) ...
    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Please log in to view the dashboard."
        return redirect('staff_login')
        
    query = request.GET.get('q', '') 
    client = LibraryClient()
    book_results = client.search_books(query)

    context = {
        'username': request.session.get('username'),
        'query': query,
        'book_results': book_results,
        'title': "Librarian Dashboard & Search"
    }
    return render(request, 'client_app/dashboard.html', context)

# 🚀 CRITICAL UPDATE: ADD_BOOK VIEW FOR FILE UPLOADS AND QUANTITY 🚀
def add_book(request: HttpRequest):
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')

    context = {
        'username': request.session.get('username'),
        'title': "Add New Book"
    }
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        
        # 1. Retrieve and safely cast total_copies to integer
        try:
            total_copies = int(request.POST.get('total_copies', 1))
            if total_copies <= 0:
                 raise ValueError
        except ValueError:
            context['error_message'] = "Total Copies must be a positive number."
            return render(request, 'client_app/add_book.html', context)

        image_file = request.FILES.get('image')
        image_path_string = None
        
        # 2. Handle File Upload (Save to local media storage)
        if image_file:
            fs = FileSystemStorage()
            # Saving the file and getting the path relative to MEDIA_ROOT
            image_path_string = fs.save(f'book_covers/{image_file.name}', image_file)
            
        client = LibraryClient()
        
        # 3. Call gRPC RPC with the CORRECT arguments (total_copies and image_path)
        response = client.create_book(
            title=title, 
            author=author, 
            isbn=isbn, 
            total_copies=total_copies, 
            image_path=image_path_string 
        )
        
        # 4. Handle Response
        context['success'] = response.success
        context['message'] = response.message
        
        if response.success:
            context['message'] += f" (New ID: {response.entity_id})"
            # Note: We don't reset form fields here, allowing user to see previous input
            
    return render(request, 'client_app/add_book.html', context)

# ----------------------------------------------------
# C. Staff Profile Management (No Change)
# ----------------------------------------------------

def staff_profile(request: HttpRequest):
    """
    Handles staff profile viewing and updates using the UpdateStaffProfile RPC.
    """
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')
    
    context = {
        'username': request.session.get('username'),
        'email': request.session.get('email', 'Update your email address'), 
        'staff_id': staff_id,
        'title': "Librarian Profile"
    }
    
    if request.method == 'POST':
        
        new_username = request.POST.get('new_username', context['username']) 
        new_email = request.POST.get('new_email', context['email'])
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        
        # 2. Basic Validation: Must supply current password
        if not current_password:
            context['error_message'] = "Security Check: You must enter your current password to save any changes."
            context['username'] = new_username 
            context['email'] = new_email
            return render(request, 'client_app/staff_profile.html', context)

        # 3. Call gRPC RPC
        client = LibraryClient()
        response = client.update_staff_profile(
            staff_id=staff_id,
            new_username=new_username,
            new_email=new_email,
            current_password=current_password,
            new_password=new_password
        )

        # 4. Process gRPC Response (StatusResponse)
        if response.success:
            context['success_message'] = response.message
            
            request.session['username'] = new_username
            if new_email:
                request.session['email'] = new_email

            if new_password:
                request.session.clear()
                request.session['login_message'] = "Password changed successfully. Please log in again."
                return redirect('staff_login')

        else:
            context['error_message'] = response.message
            context['username'] = new_username 
            context['email'] = new_email 


    # Re-render the page with success/error messages
    return render(request, 'client_app/staff_profile.html', context)