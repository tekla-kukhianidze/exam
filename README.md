# 🛋️ Furniture Store REST API (furniture_store)

ეს არის სრულად ფუნქციონალური REST API ონლაინ ავეჯის მაღაზიისთვის, აგებული Django-სა და Django REST Framework-ზე. 

---

## 🚀 1. ინსტალაცია და გაშვება

პროექტის გასაშვებად აუცილებელია: Django (API), Celery Worker და Celery Beat.

### 1.1. გარემოს მომზადება

1.  **ვირტუალური გარემოს შექმნა:**
    ```bash
    python -m venv venv
    .venv\Scripts\activate  # Windows PowerShell/CMD
    # source venv/bin/activate # Linux/macOS
    ```

2.  **დამოკიდებულებების(Dependencies) ინსტალაცია:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Redis Server-ის გაშვება:**
    * დარწმუნდით, რომ Redis Server გაშვებულია ლოკალურ მანქანაზე ნაგულისხმევ პორტზე (`6379`). Celery იყენებს Redis-ს, როგორც Broker-ს.

### 1.2. მონაცემთა ბაზის კონფიგურაცია

1.  **მოდელების მიგრაცია (ცხრილების შექმნა):**
    ```bash
    python manage.py makemigrations shop
    python manage.py migrate
    ```

2.  **სუპერმომხმარებლის შექმნა (Admin-ში შესასვლელად):**
    ```bash
    python manage.py createsuperuser
    ```
    * *შექმენით ტესტ მომხმარებელი, მაგალითად: `Username: testadmin`, `Password: adminpass`.*

### 1.3. სერვისების გაშვება

გახსენით **სამი ცალკეული ტერმინალი** და გაუშვით შემდეგი ბრძანებები:

| ფანჯარა | ბრძანება | ფუნქცია |
| :--- | :--- | :--- |
| **1. Django Server** | `python manage.py runserver` | უშვებს API-ს და Django Admin-ს. |
| **2. Celery Worker** | `celery -A furniture_store worker -l info` | ასრულებს ამოცანებს (Email-ის გაგზავნა, სტატუსის განახლება). |
| **3. Celery Beat** | `celery -A furniture_store beat -l info` | ამუშავებს პერიოდულ, დაგეგმილ ამოცანებს (`django-celery-beat`-ის მიხედვით). |

---

## 2. API ენდპოინტები

API-თან ურთიერთობა ხდება `http://127.0.0.1:8000/api/` საბაზისო URL-ით.

### 2.1. ავტორიზაცია და მომხმარებლის მართვა

* **`POST /api/register/` - მომხმარებლის რეგისტრაცია**
    * **აღწერა:** ქმნის ახალ მომხმარებელს.
    * **Request Body (JSON):**
        ```json
        {
            "username": "newuser",
            "email": "user@example.com",
            "password": "strongpassword123",
            "first_name": "მარიამ",
            "last_name": "ქავთარაძე",
            "phone": "577123456",
            "address": "თბილისი, მელიქიშვილის 5",
            "birth_date": "1995-10-25"
        }
        ```
    * **Response:** `{"username": "newuser", "email": "user@example.com", ...}` (მომხმარებლის დეტალები)

* **`POST /api/login/` - მომხმარებლის შესვლა (JWT Token-ის მიღება)**
    * **აღწერა:** აბრუნებს JWT `access` და `refresh` ტოკენებს.
    * **Request Body (JSON):**
        ```json
        {
            "username": "newuser",
            "password": "strongpassword123"
        }
        ```
    * **Response:** `{"refresh": "...", "access": "..."}`

* **`GET /api/profile/` - მომხმარებლის პროფილის ნახვა**
    * **აღწერა:** აბრუნებს მიმდინარე ავტორიზებული მომხმარებლის დეტალებს.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Response:** `{"id": 1, "username": "newuser", "email": "user@example.com", ...}`

* **`PUT /api/profile/` - მომხმარებლის პროფილის განახლება**
    * **აღწერა:** ანახლებს მიმდინარე ავტორიზებული მომხმარებლის პროფილის ინფორმაციას.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Request Body (JSON):** (შეცვალეთ მხოლოდ ის ველები, რომელთა განახლებაც გსურთ)
        ```json
        {
            "first_name": "მარი",
            "address": "თბილისი, რუსთაველის 10"
        }
        ```
    * **Response:** განახლებული მომხმარებლის დეტალები.

### 2.2. პროდუქტის კატალოგი

* **`GET /api/categories/` - ყველა კატეგორიის სია**
    * **აღწერა:** აბრუნებს ყველა აქტიურ კატეგორიას.
    * **Headers:** N/A (ყველასთვის ხელმისაწვდომია)
    * **Response:** `[{"id": 1, "name": "სკამი", "slug": "chair"}, ...]`

* **`GET /api/categories/{id}/` - კონკრეტული კატეგორიის დეტალები**
    * **Headers:** N/A

* **`GET /api/products/` - ყველა პროდუქტის სია**
    * **აღწერა:** აბრუნებს ყველა ხელმისაწვდომ პროდუქტს. მხარს უჭერს ფილტრაციას და ძებნას.
    * **Headers:** N/A (ყველასთვის ხელმისაწვდომია)
    * **Query Parameters (მაგალითები):**
        * `/api/products/?category=chair` - ფილტრავს კატეგორიის მიხედვით.
        * `/api/products/?search=დივანი` - ეძებს პროდუქტის სახელით.
        * `/api/products/?min_price=1000&max_price=2000` - ფასის დიაპაზონის მიხედვით.
    * **Response:** `[{"id": 101, "name": "მინიმალისტური სკამი", "price": "350.00", ...}, ...]`

* **`GET /api/products/{id}/` - კონკრეტული პროდუქტის დეტალები**
    * **Headers:** N/A

### 2.3. კალათა

* **`GET /api/cart/` - კალათის შიგთავსის ნახვა**
    * **აღწერა:** აბრუნებს ავტორიზებული მომხმარებლის კალათაში არსებულ ყველა პროდუქტს.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Response:** `{"id": 1, "user": 1, "items": [{"id": 1, "product": 101, "quantity": 2}, ...], "total_price": "..."}`

* **`POST /api/cart/add/` - პროდუქტის დამატება/განახლება კალათაში**
    * **აღწერა:** ამატებს ახალ პროდუქტს კალათაში ან ზრდის არსებულის რაოდენობას.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Request Body (JSON):**
        ```json
        {
            "product_id": 101, 
            "quantity": 2      
        }
        ```
    * **Response:** განახლებული კალათის დეტალები.

* **`POST /api/cart/remove/` - პროდუქტის წაშლა კალათიდან**
    * **აღწერა:** შლის პროდუქტს კალათიდან ან ამცირებს მის რაოდენობას.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Request Body (JSON):**
        ```json
        {
            "product_id": 101,  
            "quantity": 1       
        }
        ```
    * **Response:** განახლებული კალათის დეტალები.

### 2.4. შეკვეთები

* **`POST /api/orders/create/` - შეკვეთის შექმნა**
    * **აღწერა:** ქმნის ახალ შეკვეთას მომხმარებლის მიმდინარე კალათიდან. კალათა იცლება შეკვეთის შექმნის შემდეგ.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Request Body (JSON):**
        ```json
        {
            "shipping_address": "თბილისი, ჭავჭავაძის გამზირი 20, ბინა 7",
            "phone": "599123456",
            "notes": "მიწოდება სამუშაო საათებში, 10:00-დან 18:00-მდე."
        }
        ```
    * **Response:** შექმნილი შეკვეთის დეტალები.

* **`GET /api/orders/` - მომხმარებლის ყველა შეკვეთის სია**
    * **აღწერა:** აბრუნებს ავტორიზებული მომხმარებლის ყველა შეკვეთას.
    * **Headers:** `Authorization: Bearer <access_token>`
    * **Response:** `[{"id": 1, "status": "PENDING", "total_price": "...", "created_at": "...", "items": [...], ...}, ...]`

* **`GET /api/orders/{id}/` - კონკრეტული შეკვეთის დეტალები**
    * **Headers:** `Authorization: Bearer <access_token>` (მხოლოდ საკუთარ შეკვეთებზე წვდომა)

---

## 3. მენეჯმენტი და მონიტორინგი

| სისტემა | მისამართი | ფუნქცია |
| :--- | :--- | :--- |
| **Django Admin** | `http://127.0.0.1:8000/admin/` | მონაცემების ხელით მართვა (პროდუქტების დამატება, სტატუსის შეცვლა, მომხმარებლების ნახვა). |
| **DRF Login/Logout** | `http://127.0.0.1:8000/api-auth/login/` | Django REST Framework-ის Web UI-ში შესვლა/გასვლა. |
| **Flower Monitor** | `http://localhost:5555` | Celery Worker-ების სტატუსის, რიგებისა და წარსული ამოცანების რეალურ დროში მონიტორინგი. |