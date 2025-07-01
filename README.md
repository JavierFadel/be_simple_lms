# Backend Simple LMS

**be_simple_lms** adalah sistem Learning Management System (LMS) modern berbasis Django dan NinjaAPI. Proyek ini menyediakan backend lengkap untuk mengelola kursus online, pengguna, dan konten edukasi, mendukung kebutuhan guru maupun siswa.

---

## Quickstart (Docker)

1. **Salin file environment**
   ```bash
   cp .env.example .env
   # Edit .env sesuai kebutuhan (misal: SECRET_KEY, DB, dsb)
   ```
2. **Build & jalankan container**
   ```bash
   docker-compose up --build
   ```
3. **Jalankan migrasi database**
   ```bash
   docker-compose exec web python manage.py migrate
   ```
4. **Buat superuser (opsional)**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```
5. **(Opsional) Kumpulkan static files**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```
6. **Akses API**
   - API utama: http://localhost:8000/api/v1/
   - Admin Django: http://localhost:8000/admin
   - Dokumentasi API (Swagger): http://localhost:8000/api/v1/docs

---

## Fitur Utama

- **Manajemen Pengguna**
  - Registrasi & autentikasi JWT
  - Profil pengguna (edit, foto profil)
  - Lihat profil publik pengguna lain
- **Manajemen Kursus**
  - Buat, edit, hapus kursus
  - Kategori kursus
  - Penugasan guru & pendaftaran siswa
  - Batch enrollment (daftar banyak siswa sekaligus via email)
- **Manajemen Konten**
  - Tambah, edit, jadwalkan konten (video, file, dsb)
  - Publikasi/draf konten
  - Pelacakan penyelesaian konten oleh siswa
- **Pengumuman & Umpan Balik**
  - Guru dapat membuat pengumuman kursus
  - Siswa dapat memberikan feedback & rating
- **Komentar & Moderasi**
  - Komentar pada konten kursus
  - Moderasi komentar oleh guru
- **Bookmark & Pelacakan Progres**
  - Bookmark konten
  - Pelacakan penyelesaian kursus & konten
- **Statistik & Analitik**
  - Dashboard statistik pengguna & kursus
  - Analitik kursus (enrollment, completion rate, feedback, dsb)
- **Sertifikat**
  - Generate & unduh sertifikat penyelesaian kursus

---

## Struktur API
- Semua endpoint berada di bawah `/api/v1/`
- Sebagian besar aksi membutuhkan autentikasi JWT
- Ikuti konvensi RESTful (role guru & siswa terpisah jelas)

---

## Menggunakan API dengan Postman

1. **Dapatkan JWT Token**
   - Register/login via endpoint `/api/v1/register` atau `/api/v1/auth/login/`
   - Salin `access` token dari response
2. **Set Authorization di Postman**
   - Tambahkan header: `Authorization: Bearer <token>`
3. **Import Koleksi Postman**
   - (Opsional) Import file koleksi Postman yang diekspor dari repo ini
4. **Coba endpoint**
   - Contoh: `PUT /api/v1/profile/edit` untuk update profil
   - Untuk upload file, gunakan `form-data` di Postman

---

## Instalasi Manual (Tanpa Docker)
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

---

## Import Data Dummy (Opsional)
Untuk mengisi data awal dari file CSV/JSON:
```bash
cd code
python importer2.py
```

---

## Catatan
- Secara default, database menggunakan SQLite. Untuk produksi, gunakan PostgreSQL (sudah disiapkan di docker-compose).
- File media/gambar akan tersimpan di folder `code/course/` (pastikan permission folder sesuai).
- Untuk load testing, gunakan file di `load_test/locust_file.py` dengan Locust.

---

**API ini mendukung platform LMS yang fleksibel dan skalabel, cocok untuk sekolah, pusat pelatihan, atau lingkungan pembelajaran daring lainnya.**