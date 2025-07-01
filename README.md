## Backend Simple LMS

Merupakan proyek backend untuk aplikasi LMS (Learning Management System) sederhana yang dibuat untuk tujuan studi kasus pembelajaran backend development menggunakan Django dan Django Ninja.

### Konteks & Tujuan

Proyek ini menyediakan backend untuk sistem manajemen pembelajaran, di mana pengguna dapat:
- Mengelola kursus (mata kuliah)
- Mengelola anggota kursus (dosen, asisten, siswa)
- Mengelola konten kursus (materi, video, file)
- Mengelola komentar pada konten kursus

Struktur data utama:
- **Course**: Data kursus/mata kuliah.
- **CourseMember**: Relasi pengguna dengan kursus (dosen, asisten, siswa).
- **CourseContent**: Materi/konten dalam kursus.
- **Comment**: Komentar pada konten kursus.

### Endpoint & Dokumentasi

#### API (NinjaAPI)
- **/api/v1/auth/**  
  Endpoint otentikasi JWT (login, refresh, dsb) menggunakan `django-ninja-simple-jwt`.  
  Dokumentasi lebih lanjut dapat diakses melalui dokumentasi NinjaAPI (Swagger/OpenAPI) di `/api/v1/docs` (jika diaktifkan).

#### Non-API (View Biasa)
- **/**  
  Halaman utama (Hello World)
- **/testing/**  
  Menampilkan seluruh data kursus dalam format JSON.
- **/tambah/**  
  Menambah data kursus contoh (dummy).
- **/ubah/**  
  Mengubah data kursus contoh (dummy).
- **/hapus/**  
  Menghapus data kursus contoh (dummy).
- **/admin/**  
  Halaman admin Django (CRUD data secara visual).

### Struktur Data (Model)

- **Course**:  
  - name, description, price, image, teacher, created_at, updated_at
- **CourseMember**:  
  - course_id, user_id, roles (std: siswa, ast: asisten), created_at, updated_at
- **CourseContent**:  
  - name, description, video_url, file_attachment, course_id, parent_id, created_at, updated_at
- **Comment**:  
  - content_id, member_id, comment, created_at, updated_at

### Instalasi & Menjalankan Proyek

#### 1. Prasyarat
- Python 3.10+
- Docker & docker-compose (opsional, direkomendasikan)
- PostgreSQL (jika tidak menggunakan docker-compose)

#### 2. Clone Repository
```bash
git clone <repo-ini>
cd be_simple_lms
```

#### 3. Menjalankan dengan Docker Compose (Direkomendasikan)
```bash
docker-compose up --build
```
- Django akan berjalan di: http://localhost:8001
- Admin Django: http://localhost:8001/admin
- API Ninja: http://localhost:8001/api/v1/
- Database PostgreSQL: port 5551

#### 4. Menjalankan Secara Manual (Tanpa Docker)
```bash
cd code
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
- Akses di http://localhost:8000

#### 5. Import Data Dummy (Opsional)
Untuk mengisi data awal dari file CSV/JSON:
```bash
cd code
python importer2.py
```

#### 6. Testing
- Endpoint dapat diakses via Postman/cURL/dsb.
- Untuk load testing, gunakan file di `load_test/locust_file.py` dengan Locust.

### Catatan
- Secara default, database menggunakan SQLite. Untuk produksi, gunakan PostgreSQL (sudah disiapkan di docker-compose).
- File media/gambar akan tersimpan di folder `code/course/` (pastikan permission folder sesuai).