# Feature group 1

[Endpoint +1] Register: untuk memungkinkan calon user mendaftar secara langsung dengan mengisikan biodata dan data login.

[Endpoint +1] Batch Enroll Students: memungkinkan teacher untuk mendaftarkan beberapa siswa ke dalam kursus yang dimilikinya sekaligus.

[Endpoint +1] Content Comment Moderation: memungkinkan teacher untuk menentukan apakah suatu komentar pada content course-nya boleh ditampilkan atau tidak.
    - Perubahan pada tampil komentar, di mana comment yang muncul hanya yang sudah dimoderasi.

[Endpoint +1] User Activity Dashboard: Menampilkan statistik aktivitas pengguna dalam kursus. Data yang harus ditampilkan adalah:
    - Jumlah course yang diikuti sebagai student
    - Jumlah course yang dibuat
    - Jumlah komentar yang pernah ditulis
    - Jumlah content yang diselesaikan (jika fitur content completion dibuat)

[Endpoint +1] Course Analytics: Menyediakan statistik course, meliputi:
    - Jumlah member pada course tersebut
    - Jumlah konten pada course tersebut
    - Jumlah komentar pada course tersebut
    - Jumlah feedback pada course tersebut (jika fitur feedback dibuat)

[Improve +1] Content Scheduling: Teacher dapat menjadwalkan konten untuk dirilis pada waktu tertentu saja. Di luar waktu tersebut, konten tidak boleh muncul pada saat di-list.

[Improve +1] Course Enrollment Limits: Menetapkan batasan jumlah pendaftar course:
    - Satu student hanya bisa enroll sekali pada course yang sama
    - Teacher bisa menentukan jumlah maksimal student
    - Jika kuota penuh, tidak ada lagi studen yang bisa masuk

[Fitur | Endpoint +3] Course Completion Certificates: menampilkan halaman HTML berupa sertifikat bagi pengguna yang menyelesaikan kursus.
    -  Menyelesaikan fitur ini sama dengan menyelesaikan 3 endpoint dengan syarat halaman sertifikatnya didesain dengan baik.

# Feature group 2

[Fitur +2] Manajemen Profil Pengguna: Memungkinkan user untuk mengedit profilnya sendiri dan menampilkan profil dari semua user berdasarkan ID-nya.
    [Endpoint] Show Profile: untuk menampilkan profil lengkap dari seorang pengguna tertentu meliputi Nama depan, Nama belakang, Email, Handphone, Deskripsi, Foto Profil, list course yang diikuti, dan list course yang dibuat.
    [Endpoint] Edit Profil: untuk mengedit data kita sendiri (user yang sedang login) meliputi: Edit Nama depan, Nama belakang, Email, Handphone, Deskripsi, dan Foto Profil

[Fitur +4] Course Announcements merupakan fitur tambahan agar seorang teacher bisa memberikan pengumuman khusus pada course tertentu yang akan muncul pada tanggal tertentu. Endpoint yang perlu ditambahakan untuk fitur ini adalah:
    [Endpoint] Create announcement: untuk menambahkan pengumuman pada course tertentu (hanya teacher yang dapat membuat announcement)
    [Endpoint] Show announcement: untuk menampilkan semua pengumuman pada course tertentu (teacher dan student dapat menampilkan announcement)
    [Endpoint] Edit announcement: untuk mengedit announcement (hanya teacher yang dapat mengedit announcement)
    [Endpoint] Delete announcement: endpoint untuk menghapus announcement (hanya teacher yang dapat menghapus announcement)

[Fitur +3] Content Completion Tracking: Menambahkan fitur agar student bisa menandai content yang sudah diselesaikan. Fitur ini memerlukan tabel tambahan yaitu tabel completion tracking.
    [Endpoint] Add completion tracking: student dapat menandai bahwa suatu konten sudah diselesaikan.
    [Endpoint] Show completion: student dapat menampilkan list completion pada suatu course yang dia ikuti
    [Endpoint] Delete completion: student dapat menghapus data completion-nya sendiri.

[Fitur +4] Course Feedback: Memungkinkan teacher mengumpulkan umpan balik dari student tentang kursus yang telah diikuti.
    [Endpoint] Add Feedback: untuk menambahkan feedback pada course tertentu
    [Endpoint] Show feedback: untuk menampilkan semua feedback pada course tertentu
    [Endpoint]Edit feedback: student dapat mengedit feedback yang sudah ditulisnya
    [Endpoint] Delete feedback: student dapat menghapus feedback yang sudah ditulisnya

[Fitur +3] Content Bookmarking: Memungkinkan pengguna menandai konten kursus untuk referensi di masa mendatang.
    [Endpoint] Add bookmarking: untuk student membuat bookmark pada course content yang bisa diakses.
    [Endpoint] Show bookmark: untuk menampilkan semua bookmark yang dibuat oleh student tersebut. Bookmark harus menampilkan konten dan course-nya juga.
    [Endpoint] Delete bookmark: untuk menghapus bookmark yang pernah dibuat student tersebut.

[Fitur +4] Course Categories Management: Memungkinkan teacher untuk menambah, mengedit, dan menghapus kategori dan menambahkan kategori tersebut pada course yang dibuat.
    [Endpoint] Add Category: untuk membuat kategori baru
    [Endpoint] Show category: untuk menampilkan semua kategori yang pernah dibuat (oleh semua user)
    [Endpoint] Delete category: untuk menghapus kategori yang pernah dibuat oleh user tersebut.
    [Improve] Add category column to course: pada saat membuat dan mengedit course, ada tambahan kolom course yang sifatnya boleh null.

[Fitur +2] Content Approval Workflow: Menetapkan status publikasi dari sebuah konten.
    [Endpoint] Update content: untuk teacher mengupdate konten yang pernah dibuat
    [Improve] Publish | unpublish content: konten yang belum dipublished tidak muncul jika yang melakukan request adalah student, tapi tetap muncul jika yang melakukan request adalah teacher.

[Fitur +2] Content Approval Workflow: Menetapkan status publikasi dari sebuah konten.
    [Endpoint] Update content: untuk teacher mengupdate konten yang pernah dibuat
    [Improve] Publish | unpublish content: konten yang belum dipublish tidak muncul jika yang melakukan request adalah student, tapi tetap muncul jika yang melakukan request adalah teacher.

[Fitur +4] API Rate Limiting: Mengimplementasikan rate limiting untuk melindungi API dari penyalahgunaan.
    [Improve] Limit Register: 1 IP yang sama hanya bisa melakukan 5 x register di hari yang sama.
    [Improve] Limit comment: 1 student hanya dapat posting maks 10 komentar dalam 1 jam
    [Improve] Limit course creation: 1 teacher hanya dapat create 1 course dalam 1 hari
    [Improve] Limit content creation: 1 teacher hanya dapat create 10 content dalam 1 jam