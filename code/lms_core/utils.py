import re
from django.http import HttpRequest
from django.utils import timezone
from datetime import timedelta, date
from lms_core.models import RegistrationAttempt
from ninja.errors import HttpError
from lms_core.models import CommentRateLimit, CourseCreationLimit, ContentCreationLimit

def calculator(a, b, operator):
    if operator == '+':
        return a + b
    elif operator == '-':
        return a - b
    elif operator == 'x':
        return a * b
    elif operator == '/':
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError("Invalid operator")

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # Memeriksa huruf besar
        return False
    if not re.search(r"[a-z]", password):  # Memeriksa huruf kecil
        return False
    if not re.search(r"[0-9]", password):  # Memeriksa angka
        return False
    if not re.search(r"[!@#$%^&*()]", password):  # Memeriksa karakter khusus
        return False
    return True

def get_client_ip(request: HttpRequest) -> str:
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_registration_rate_limit(request: HttpRequest):
    """Check if IP has exceeded registration attempts (5 per day)"""
    ip_address = get_client_ip(request)
    today = timezone.now().date()
    
    # Count today's attempts
    attempts_today = RegistrationAttempt.objects.filter(
        ip_address=ip_address,
        attempted_at__date=today
    ).count()
    
    if attempts_today >= 5:
        raise HttpError(429, "Registration limit exceeded. Maximum 5 registrations per day per IP.")
    
    # Record this attempt
    RegistrationAttempt.objects.create(ip_address=ip_address)

def check_comment_rate_limit(user):
    """Check if user has exceeded comment limit (10 per hour)"""
    current_time = timezone.now()
    hour_ago = current_time - timedelta(hours=1)
    
    # Get or create rate limit record
    rate_limit, created = CommentRateLimit.objects.get_or_create(
        user=user,
        hour_started__gte=hour_ago,
        defaults={
            'hour_started': current_time,
            'comment_count': 0
        }
    )
    
    # If record is older than 1 hour, reset
    if rate_limit.hour_started < hour_ago:
        rate_limit.hour_started = current_time
        rate_limit.comment_count = 0
        rate_limit.save()
    
    if rate_limit.comment_count >= 10:
        raise HttpError(429, "Comment limit exceeded. Maximum 10 comments per hour.")
    
    # Increment counter
    rate_limit.comment_count += 1
    rate_limit.save()

def check_course_creation_limit(teacher):
    """Check if teacher has exceeded course creation limit (1 per day)"""
    today = date.today()
    
    limit_record, created = CourseCreationLimit.objects.get_or_create(
        teacher=teacher,
        date_created=today,
        defaults={'courses_created': 0}
    )
    
    if limit_record.courses_created >= 1:
        raise HttpError(429, "Course creation limit exceeded. Maximum 1 course per day.")
    
    # Increment counter
    limit_record.courses_created += 1
    limit_record.save()

def check_content_creation_limit(teacher):
    """Check if teacher has exceeded content creation limit (10 per hour)"""
    current_time = timezone.now()
    hour_ago = current_time - timedelta(hours=1)
    
    # Get or create rate limit record
    rate_limit, created = ContentCreationLimit.objects.get_or_create(
        teacher=teacher,
        hour_started__gte=hour_ago,
        defaults={
            'hour_started': current_time,
            'content_count': 0
        }
    )
    
    # If record is older than 1 hour, reset
    if rate_limit.hour_started < hour_ago:
        rate_limit.hour_started = current_time
        rate_limit.content_count = 0
        rate_limit.save()
    
    if rate_limit.content_count >= 10:
        raise HttpError(429, "Content creation limit exceeded. Maximum 10 contents per hour.")
    
    # Increment counter
    rate_limit.content_count += 1
    rate_limit.save()

def is_teacher_of_course(user, course):
    """Check if user is the teacher of the course"""
    return course.teacher == user

def is_member_of_course(user, course):
    """Check if user is a member of the course"""
    return course.is_member(user)

def can_view_content(user, content):
    """Check if user can view content based on publish status and role"""
    # Teacher can always view
    if content.course_id.teacher == user:
        return True
    
    # Students can only view published content
    if content.status == 'published':
        return True
    
    return False