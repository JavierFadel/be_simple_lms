from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class CourseCategory(models.Model):
    name = models.CharField("Nama Kategori", max_length=100, unique=True)
    description = models.TextField("Deskripsi", blank=True, null=True)
    created_by = models.ForeignKey(User, verbose_name="Dibuat oleh", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kategori Kursus"
        verbose_name_plural = "Kategori Kursus"
        ordering = ["name"]

# Enhanced Course model
class Course(models.Model):
    name = models.CharField("Nama Kursus", max_length=255)
    description = models.TextField("Deskripsi")
    price = models.IntegerField("Harga")
    image = models.ImageField("Gambar", upload_to="course", blank=True, null=True)
    teacher = models.ForeignKey(User, verbose_name="Pengajar", on_delete=models.RESTRICT)
    max_enrollment = models.IntegerField("Maximum Enrollment", null=True, blank=True)
    category = models.ForeignKey(CourseCategory, verbose_name="Kategori", on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Data Mata Kuliah"
        ordering = ["-created_at"]

    def is_member(self, user):
        return CourseMember.objects.filter(course_id=self, user_id=user).exists()

ROLE_OPTIONS = [('std', "Siswa"), ('ast', "Asisten")]

class CourseMember(models.Model):
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    user_id = models.ForeignKey(User, verbose_name="siswa", on_delete=models.RESTRICT)
    roles = models.CharField("peran", max_length=3, choices=ROLE_OPTIONS, default='std')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscriber Matkul"
        verbose_name_plural = "Subscriber Matkul"
        unique_together = ['course_id', 'user_id']

    def __str__(self) -> str:
        return f"{self.id} {self.course_id} : {self.user_id}"

# Enhanced CourseContent with publish status
CONTENT_STATUS = [('draft', 'Draft'), ('published', 'Published')]

class CourseContent(models.Model):
    name = models.CharField("judul konten", max_length=200)
    description = models.TextField("deskripsi", default='-')
    video_url = models.CharField('URL Video', max_length=200, null=True, blank=True)
    file_attachment = models.FileField("File", null=True, blank=True)
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    parent_id = models.ForeignKey("self", verbose_name="induk", 
                                on_delete=models.RESTRICT, null=True, blank=True)
    status = models.CharField("Status", max_length=10, choices=CONTENT_STATUS, default='draft')
    scheduled_release = models.DateTimeField("Scheduled Release", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konten Matkul"
        verbose_name_plural = "Konten Matkul"

    def __str__(self) -> str:
        return f'{self.course_id} {self.name}'

class Comment(models.Model):
    content_id = models.ForeignKey(CourseContent, verbose_name="konten", on_delete=models.CASCADE)
    member_id = models.ForeignKey(CourseMember, verbose_name="pengguna", on_delete=models.CASCADE)
    comment = models.TextField('komentar')
    is_approved = models.BooleanField("Is Approved", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"

    def __str__(self) -> str:
        return "Komen: "+self.member_id.user_id+"-"+self.comment

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Format nomor telepon: '+999999999'. Maksimal 15 digit.")
    phone_number = models.CharField("Nomor Telepon", validators=[phone_regex], max_length=17, blank=True, null=True)
    description = models.TextField("Deskripsi", blank=True, null=True)
    profile_picture = models.ImageField("Foto Profil", upload_to="profiles/", blank=True, null=True)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    class Meta:
        verbose_name = "Profil Pengguna"
        verbose_name_plural = "Profil Pengguna"

class Comment(models.Model):
    content_id = models.ForeignKey(CourseContent, verbose_name="konten", on_delete=models.CASCADE)
    member_id = models.ForeignKey(CourseMember, verbose_name="pengguna", on_delete=models.CASCADE)
    comment = models.TextField('komentar')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"

    def __str__(self) -> str:
        return f"Komen: {self.member_id.user_id}-{self.comment}"
    
class CourseAnnouncement(models.Model):
    title = models.CharField("Judul Pengumuman", max_length=200)
    content = models.TextField("Isi Pengumuman")
    course = models.ForeignKey(Course, verbose_name="Kursus", on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, verbose_name="Dibuat oleh", on_delete=models.CASCADE)
    publish_date = models.DateTimeField("Tanggal Publikasi")
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    class Meta:
        verbose_name = "Pengumuman"
        verbose_name_plural = "Pengumuman"
        ordering = ["-publish_date"]

    def __str__(self):
        return f"{self.course.name} - {self.title}"
    
class ContentCompletion(models.Model):
    student = models.ForeignKey(User, verbose_name="Siswa", on_delete=models.CASCADE)
    content = models.ForeignKey(CourseContent, verbose_name="Konten", on_delete=models.CASCADE)
    completed_at = models.DateTimeField("Diselesaikan pada", auto_now_add=True)

    class Meta:
        verbose_name = "Penyelesaian Konten"
        verbose_name_plural = "Penyelesaian Konten"
        unique_together = ['student', 'content']

    def __str__(self):
        return f"{self.student.username} - {self.content.name}"
    
class CourseFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    student = models.ForeignKey(User, verbose_name="Siswa", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, verbose_name="Kursus", on_delete=models.CASCADE)
    rating = models.IntegerField("Rating", choices=RATING_CHOICES)
    feedback_text = models.TextField("Umpan Balik")
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    class Meta:
        verbose_name = "Umpan Balik"
        verbose_name_plural = "Umpan Balik"
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.username} - {self.course.name} ({self.rating}/5)"
    
class ContentBookmark(models.Model):
    student = models.ForeignKey(User, verbose_name="Siswa", on_delete=models.CASCADE)
    content = models.ForeignKey(CourseContent, verbose_name="Konten", on_delete=models.CASCADE)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Bookmark Konten"
        verbose_name_plural = "Bookmark Konten"
        unique_together = ['student', 'content']

    def __str__(self):
        return f"{self.student.username} - {self.content.name}"
    
# Rate Limiting Models
class RegistrationAttempt(models.Model):
    ip_address = models.GenericIPAddressField("Alamat IP")
    attempted_at = models.DateTimeField("Waktu Percobaan", auto_now_add=True)
    
    class Meta:
        verbose_name = "Percobaan Registrasi"
        verbose_name_plural = "Percobaan Registrasi"

class CommentRateLimit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment_count = models.IntegerField("Jumlah Komentar", default=0)
    hour_started = models.DateTimeField("Jam Mulai")
    
    class Meta:
        verbose_name = "Batas Komentar"
        verbose_name_plural = "Batas Komentar"

class CourseCreationLimit(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    courses_created = models.IntegerField("Kursus Dibuat", default=0)
    date_created = models.DateField("Tanggal")
    
    class Meta:
        verbose_name = "Batas Pembuatan Kursus"
        verbose_name_plural = "Batas Pembuatan Kursus"
        unique_together = ['teacher', 'date_created']

class ContentCreationLimit(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    content_count = models.IntegerField("Jumlah Konten", default=0)
    hour_started = models.DateTimeField("Jam Mulai")
    
    class Meta:
        verbose_name = "Batas Pembuatan Konten"
        verbose_name_plural = "Batas Pembuatan Konten"