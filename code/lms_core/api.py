from ninja import NinjaAPI, UploadedFile, File
from ninja.responses import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from lms_core.schema import *
from lms_core.models import *
from lms_core.utils import *
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja.pagination import paginate, PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken

apiv1 = NinjaAPI()
apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = JWTAuth()

# =================== USER PROFILE MANAGEMENT ===================

def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

@apiv1.post("/register", response=UserRegisterOut)
def register_user(request, data: UserRegisterIn, profile_picture: UploadedFile = File(None)):
    """Register new user with rate limiting"""
    
    # FIXME: matikan rate limiter untuk testing
    # Check rate limiting
    # check_registration_rate_limit(request)
    
    # Validate password
    if not validate_password(data.password):
        raise HttpError(400, "Password harus minimal 8 karakter dengan huruf besar, kecil, angka, dan karakter khusus")
    
    # Check if username/email already exists
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username sudah digunakan")
    
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email sudah digunakan")
    
    # Create user
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name
    )
    
    # Create user profile
    profile_data = {
        'user': user,
        'phone_number': data.phone_number,
        'description': data.description
    }
    
    if profile_picture:
        profile_data['profile_picture'] = profile_picture
    
    UserProfile.objects.create(**profile_data)

    token = generate_tokens_for_user(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "access": token['access'],
        "refresh": token['refresh'],
        "message": "Registrasi berhasil"
    }

@apiv1.get("/profile/{user_id}", response=UserFullProfileOut, auth=apiAuth)
def show_profile(request, user_id: int):

    """Show full profile of a user including courses"""
    user = get_object_or_404(User, id=user_id)
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile_data = None
    if profile:
        profile_data = {
            "id": profile.id,
            "phone_number": profile.phone_number,
            "description": profile.description,
            "profile_picture": profile.profile_picture.url if profile.profile_picture else None,
        }
    
    # Get courses enrolled and created
    courses_enrolled = Course.objects.filter(coursemember__user_id=user)
    courses_created = Course.objects.filter(teacher=user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile": profile_data,
        "courses_enrolled": courses_enrolled,
        "courses_created": courses_created
    }

@apiv1.put("/profile/edit", response=MessageResponse, auth=apiAuth)
def edit_profile(request, data: UserProfileIn, profile_picture: UploadedFile = File(None)):
    """Edit current user's profile"""
    user = request.auth
    
    # Update user basic info
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.email is not None:
        user.email = data.email
    user.save()
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Update profile info
    if data.phone_number is not None:
        profile.phone_number = data.phone_number
    if data.description is not None:
        profile.description = data.description
    if profile_picture:
        profile.profile_picture = profile_picture
    
    profile.save()
    
    return {"message": "Profile updated successfully"}

# =================== COURSE CATEGORIES ===================

@apiv1.post("/categories", response=CourseCategoryOut, auth=apiAuth)
def create_category(request, data: CourseCategoryIn):
    """Create a new course category"""
    category = CourseCategory.objects.create(
        name=data.name,
        description=data.description,
        created_by=request.auth
    )
    return category

@apiv1.get("/categories", response=List[CourseCategoryOut])
def list_categories(request):
    """List all categories"""
    return CourseCategory.objects.all()

@apiv1.delete("/categories/{category_id}", response=MessageResponse, auth=apiAuth)
def delete_category(request, category_id: int):
    """Delete a category (only by creator)"""
    category = get_object_or_404(CourseCategory, id=category_id)
    
    if category.created_by != request.auth:
        raise HttpError(403, "You can only delete your own categories")
    
    category.delete()
    return {"message": "Category deleted successfully"}

# =================== COURSE ANNOUNCEMENTS ===================

@apiv1.post("/courses/{course_id}/announcements", response=CourseAnnouncementOut, auth=apiAuth)
def create_announcement(request, course_id: int, data: CourseAnnouncementIn):
    """Create course announcement (teacher only)"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can create announcements")
    
    announcement = CourseAnnouncement.objects.create(
        title=data.title,
        content=data.content,
        course=course,
        created_by=request.auth,
        publish_date=data.publish_date
    )
    return announcement

@apiv1.get("/courses/{course_id}/announcements", response=List[CourseAnnouncementOut], auth=apiAuth)
def list_announcements(request, course_id: int):
    """List course announcements"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is teacher or member
    if not (is_teacher_of_course(request.auth, course) or is_member_of_course(request.auth, course)):
        raise HttpError(403, "You must be enrolled in this course")
    
    # Show only published announcements (publish_date <= now)
    announcements = CourseAnnouncement.objects.filter(
        course=course,
        publish_date__lte=timezone.now()
    )
    return announcements

@apiv1.put("/courses/{course_id}/announcements/{announcement_id}", response=CourseAnnouncementOut, auth=apiAuth)
def update_announcement(request, course_id: int, announcement_id: int, data: CourseAnnouncementUpdate):
    """Update announcement (teacher only)"""
    course = get_object_or_404(Course, id=course_id)
    announcement = get_object_or_404(CourseAnnouncement, id=announcement_id, course=course)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can edit announcements")
    
    if data.title is not None:
        announcement.title = data.title
    if data.content is not None:
        announcement.content = data.content
    if data.publish_date is not None:
        announcement.publish_date = data.publish_date
    
    announcement.save()
    return announcement

@apiv1.delete("/courses/{course_id}/announcements/{announcement_id}", response=MessageResponse, auth=apiAuth)
def delete_announcement(request, course_id: int, announcement_id: int):
    """Delete announcement (teacher only)"""
    course = get_object_or_404(Course, id=course_id)
    announcement = get_object_or_404(CourseAnnouncement, id=announcement_id, course=course)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can delete announcements")
    
    announcement.delete()
    return {"message": "Announcement deleted successfully"}

# =================== CONTENT COMPLETION TRACKING ===================

@apiv1.post("/content/{content_id}/complete", response=ContentCompletionOut, auth=apiAuth)
def mark_content_complete(request, content_id: int):
    """Mark content as completed by student"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    # Check if user is enrolled in the course
    if not is_member_of_course(request.auth, content.course_id):
        raise HttpError(403, "You must be enrolled in this course")
    
    # Check if content is published
    if not can_view_content(request.auth, content):
        raise HttpError(403, "Content is not available")
    
    completion, created = ContentCompletion.objects.get_or_create(
        student=request.auth,
        content=content
    )
    
    if not created:
        raise HttpError(400, "Content already marked as completed")
    
    return completion

@apiv1.get("/courses/{course_id}/completions", response=List[ContentCompletionOut], auth=apiAuth)
def list_completions(request, course_id: int):
    """List user's completions for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_member_of_course(request.auth, course):
        raise HttpError(403, "You must be enrolled in this course")
    
    completions = ContentCompletion.objects.filter(
        student=request.auth,
        content__course_id=course
    )
    return completions

@apiv1.delete("/content/{content_id}/complete", response=MessageResponse, auth=apiAuth)
def remove_completion(request, content_id: int):
    """Remove content completion"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    completion = get_object_or_404(ContentCompletion, student=request.auth, content=content)
    completion.delete()
    
    return {"message": "Completion removed successfully"}

# =================== COURSE FEEDBACK ===================

@apiv1.post("/courses/{course_id}/feedback", response=CourseFeedbackOut, auth=apiAuth)
def create_feedback(request, course_id: int, data: CourseFeedbackIn):
    """Create course feedback"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_member_of_course(request.auth, course):
        raise HttpError(403, "You must be enrolled in this course")
    
    feedback, created = CourseFeedback.objects.update_or_create(
        student=request.auth,
        course=course,
        defaults={
            'rating': data.rating,
            'feedback_text': data.feedback_text
        }
    )
    
    return feedback

@apiv1.get("/courses/{course_id}/feedback", response=List[CourseFeedbackOut], auth=apiAuth)
def list_feedback(request, course_id: int):
    """List all feedback for a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Only teacher and enrolled students can view feedback
    if not (is_teacher_of_course(request.auth, course) or is_member_of_course(request.auth, course)):
        raise HttpError(403, "Access denied")
    
    feedback = CourseFeedback.objects.filter(course=course)
    return feedback

@apiv1.put("/courses/{course_id}/feedback", response=CourseFeedbackOut, auth=apiAuth)
def update_feedback(request, course_id: int, data: CourseFeedbackUpdate):
    """Update own feedback"""
    course = get_object_or_404(Course, id=course_id)
    feedback = get_object_or_404(CourseFeedback, student=request.auth, course=course)
    
    if data.rating is not None:
        feedback.rating = data.rating
    if data.feedback_text is not None:
        feedback.feedback_text = data.feedback_text
    
    feedback.save()
    return feedback

@apiv1.delete("/courses/{course_id}/feedback", response=MessageResponse, auth=apiAuth)
def delete_feedback(request, course_id: int):
    """Delete own feedback"""
    course = get_object_or_404(Course, id=course_id)
    feedback = get_object_or_404(CourseFeedback, student=request.auth, course=course)
    feedback.delete()
    
    return {"message": "Feedback deleted successfully"}

# =================== CONTENT BOOKMARKING ===================

@apiv1.post("/content/{content_id}/bookmark", response=ContentBookmarkOut, auth=apiAuth)
def create_bookmark(request, content_id: int):
    """Create content bookmark"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not is_member_of_course(request.auth, content.course_id):
        raise HttpError(403, "You must be enrolled in this course")
    
    if not can_view_content(request.auth, content):
        raise HttpError(403, "Content is not available")
    
    bookmark, created = ContentBookmark.objects.get_or_create(
        student=request.auth,
        content=content
    )
    
    if not created:
        raise HttpError(400, "Content already bookmarked")
    
    return bookmark

@apiv1.get("/bookmarks", response=List[ContentBookmarkOut], auth=apiAuth)
def list_bookmarks(request):
    """List user's bookmarks"""
    bookmarks = ContentBookmark.objects.filter(student=request.auth)
    return bookmarks

@apiv1.delete("/content/{content_id}/bookmark", response=MessageResponse, auth=apiAuth)
def delete_bookmark(request, content_id: int):
    """Delete bookmark"""
    content = get_object_or_404(CourseContent, id=content_id)
    bookmark = get_object_or_404(ContentBookmark, student=request.auth, content=content)
    bookmark.delete()
    
    return {"message": "Bookmark deleted successfully"}

# =================== ENHANCED COURSE MANAGEMENT ===================

@apiv1.post("/courses", response=CourseSchemaOut, auth=apiAuth)
def create_course(request, data: CourseSchemaIn, image: UploadedFile = File(None)):
    """Create new course with rate limiting"""
    check_course_creation_limit(request.auth)
    
    course_data = {
        'name': data.name,
        'description': data.description,
        'price': data.price,
        'teacher': request.auth
    }
    
    if data.category_id:
        category = get_object_or_404(CourseCategory, id=data.category_id)
        course_data['category'] = category
    
    if image:
        course_data['image'] = image
    
    course = Course.objects.create(**course_data)
    return course

@apiv1.get("/courses", response=List[CourseSchemaOut])
@paginate(PageNumberPagination, page_size=10)
def list_courses(request):
    """List all courses"""
    return Course.objects.all()

@apiv1.get("/courses/{course_id}", response=CourseSchemaOut, auth=apiAuth)
def get_course(request, course_id: int):
    """Get course details"""
    course = get_object_or_404(Course, id=course_id)
    return course

# =================== ENHANCED CONTENT MANAGEMENT ===================

@apiv1.post("/courses/{course_id}/content", response=CourseContentFull, auth=apiAuth)
def list_course_content(request, course_id: int):
    """List course content with publish status and scheduling filtering"""
    course = get_object_or_404(Course, id=course_id)
    
    if not (is_teacher_of_course(request.auth, course) or is_member_of_course(request.auth, course)):
        raise HttpError(403, "Access denied")
    
    contents = CourseContent.objects.filter(course_id=course)
    
    # Filter content for students
    if not is_teacher_of_course(request.auth, course):
        # Only show published content
        contents = contents.filter(status='published')
        # Only show content where scheduled_release is null or in the past
        contents = contents.filter(
            models.Q(scheduled_release__isnull=True) | 
            models.Q(scheduled_release__lte=timezone.now())
        )
    
    return contents

@apiv1.get("/courses/{course_id}/content", response=List[CourseContentFull], auth=apiAuth)
def list_course_content(request, course_id: int):
    """List course content with publish status filtering"""
    course = get_object_or_404(Course, id=course_id)
    
    if not (is_teacher_of_course(request.auth, course) or is_member_of_course(request.auth, course)):
        raise HttpError(403, "Access denied")
    
    contents = CourseContent.objects.filter(course_id=course)
    
    # Filter by publish status for students
    if not is_teacher_of_course(request.auth, course):
        contents = contents.filter(status='published')
    
    return contents

@apiv1.put("/content/{content_id}", response=CourseContentFull, auth=apiAuth)
def update_content(request, content_id: int, data: CourseContentUpdate, file_attachment: UploadedFile = File(None)):
    """Update content (teacher only)"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not is_teacher_of_course(request.auth, content.course_id):
        raise HttpError(403, "Only teachers can update content")
    
    if data.name is not None:
        content.name = data.name
    if data.description is not None:
        content.description = data.description
    if data.video_url is not None:
        content.video_url = data.video_url
    if data.status is not None:
        content.status = data.status
    if file_attachment:
        content.file_attachment = file_attachment
    
    content.save()
    return content

@apiv1.patch("/content/{content_id}/publish", response=MessageResponse, auth=apiAuth)
def toggle_content_publish(request, content_id: int):
    """Toggle content publish status"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not is_teacher_of_course(request.auth, content.course_id):
        raise HttpError(403, "Only teachers can publish/unpublish content")
    
    content.status = 'published' if content.status == 'draft' else 'draft'
    content.save()
    
    return {"message": f"Content {content.status} successfully"}

# =================== ENHANCED COMMENT SYSTEM ===================

@apiv1.post("/content/{content_id}/comments", response=CourseCommentOut, auth=apiAuth)
def create_comment(request, content_id: int, data: CourseCommentIn):
    """Create comment with rate limiting"""
    check_comment_rate_limit(request.auth)
    
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not is_member_of_course(request.auth, content.course_id):
        raise HttpError(403, "You must be enrolled in this course")
    
    if not can_view_content(request.auth, content):
        raise HttpError(403, "Content is not available")
    
    # Get user's course membership
    member = get_object_or_404(CourseMember, course_id=content.course_id, user_id=request.auth)
    
    comment = Comment.objects.create(
        content_id=content,
        member_id=member,
        comment=data.comment
    )
    
    return comment

@apiv1.get("/content/{content_id}/comments", response=List[CourseCommentOut], auth=apiAuth)
def list_comments(request, content_id: int):
    """List content comments (only approved for students)"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not (is_teacher_of_course(request.auth, content.course_id) or is_member_of_course(request.auth, content.course_id)):
        raise HttpError(403, "Access denied")
    
    if not can_view_content(request.auth, content):
        raise HttpError(403, "Content is not available")
    
    # Teachers see all comments, students see only approved ones
    if is_teacher_of_course(request.auth, content.course_id):
        comments = Comment.objects.filter(content_id=content)
    else:
        comments = get_approved_comments(content)
    
    return comments

# =================== STATISTICS & ANALYTICS ===================

@apiv1.get("/courses/{course_id}/stats", response=CourseStatsOut, auth=apiAuth)
def get_course_stats(request, course_id: int):
    """Get course statistics"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can view course statistics")
    
    total_students = CourseMember.objects.filter(course_id=course).count()
    total_contents = CourseContent.objects.filter(course_id=course).count()
    total_announcements = CourseAnnouncement.objects.filter(course=course).count()
    
    # Calculate completion rate
    if total_contents > 0 and total_students > 0:
        total_possible_completions = total_contents * total_students
        actual_completions = ContentCompletion.objects.filter(
            content__course_id=course
        ).count()
        completion_rate = (actual_completions / total_possible_completions) * 100
    else:
        completion_rate = 0.0
    
    return {
        "total_students": total_students,
        "total_contents": total_contents,
        "total_announcements": total_announcements,
        "completion_rate": completion_rate
    }

@apiv1.get("/profile/stats", response=UserStatsOut, auth=apiAuth)
def get_user_stats(request):
    """Get user statistics"""
    user = request.auth
    
    courses_enrolled = CourseMember.objects.filter(user_id=user).count()
    courses_created = Course.objects.filter(teacher=user).count()
    contents_completed = ContentCompletion.objects.filter(student=user).count()
    bookmarks_count = ContentBookmark.objects.filter(student=user).count()
    
    return {
        "courses_enrolled": courses_enrolled,
        "courses_created": courses_created,
        "contents_completed": contents_completed,
        "bookmarks_count": bookmarks_count
    }

# =================== BATCH ENROLLMENT ===================

@apiv1.post("/courses/{course_id}/batch-enroll", response=MessageResponse, auth=apiAuth)
def batch_enroll_students(request, course_id: int, data: BatchEnrollIn):
    """Batch enroll students to course (teacher only)"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can enroll students")
    
    enrolled_count = 0
    failed_enrollments = []
    
    for email in data.student_emails:
        try:
            user = User.objects.get(email=email)
            member, created = CourseMember.objects.get_or_create(
                course_id=course,
                user_id=user,
                defaults={'roles': 'std'}
            )
            if created:
                enrolled_count += 1
        except User.DoesNotExist:
            failed_enrollments.append(f"User with email {email} not found")
        except Exception as e:
            failed_enrollments.append(f"Failed to enroll {email}: {str(e)}")
    
    message = f"Successfully enrolled {enrolled_count} students"
    if failed_enrollments:
        message += f". Failed: {', '.join(failed_enrollments)}"
    
    return {"message": message}

# =================== COMMENT MODERATION ===================

@apiv1.patch("/content/{content_id}/comments/{comment_id}/moderate", response=MessageResponse, auth=apiAuth)
def moderate_comment(request, content_id: int, comment_id: int, data: CommentModerationIn):
    """Moderate comment (teacher only)"""
    content = get_object_or_404(CourseContent, id=content_id)
    comment = get_object_or_404(Comment, id=comment_id, content_id=content)
    
    if not is_teacher_of_course(request.auth, content.course_id):
        raise HttpError(403, "Only teachers can moderate comments")
    
    comment.is_approved = data.is_approved
    comment.save()
    
    status = "approved" if data.is_approved else "hidden"
    return {"message": f"Comment {status} successfully"}

# =================== ENHANCED USER STATS ===================

@apiv1.get("/profile/activity-dashboard", response=UserActivityDashboardOut, auth=apiAuth)
def get_user_activity_dashboard(request):
    """Get comprehensive user activity dashboard"""
    user = request.auth
    
    courses_enrolled = CourseMember.objects.filter(user_id=user).count()
    courses_created = Course.objects.filter(teacher=user).count()
    contents_completed = ContentCompletion.objects.filter(student=user).count()
    bookmarks_count = ContentBookmark.objects.filter(student=user).count()
    comments_written = Comment.objects.filter(member_id__user_id=user).count()
    
    return {
        "courses_enrolled": courses_enrolled,
        "courses_created": courses_created,
        "contents_completed": contents_completed,
        "bookmarks_count": bookmarks_count,
        "comments_written": comments_written
    }

# =================== ENHANCED COURSE ANALYTICS ===================

@apiv1.get("/courses/{course_id}/analytics", response=CourseAnalyticsOut, auth=apiAuth)
def get_course_analytics(request, course_id: int):
    """Get comprehensive course analytics"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can view course analytics")
    
    total_students = CourseMember.objects.filter(course_id=course).count()
    total_contents = CourseContent.objects.filter(course_id=course).count()
    total_announcements = CourseAnnouncement.objects.filter(course=course).count()
    total_comments = Comment.objects.filter(content_id__course_id=course).count()
    total_feedback = CourseFeedback.objects.filter(course=course).count()
    
    # Calculate completion rate
    if total_contents > 0 and total_students > 0:
        total_possible_completions = total_contents * total_students
        actual_completions = ContentCompletion.objects.filter(
            content__course_id=course
        ).count()
        completion_rate = (actual_completions / total_possible_completions) * 100
    else:
        completion_rate = 0.0
    
    # Calculate average rating
    avg_rating = CourseFeedback.objects.filter(course=course).aggregate(
        avg_rating=models.Avg('rating')
    )['avg_rating'] or 0.0
    
    return {
        "total_students": total_students,
        "total_contents": total_contents,
        "total_announcements": total_announcements,
        "total_comments": total_comments,
        "total_feedback": total_feedback,
        "completion_rate": completion_rate,
        "average_rating": round(avg_rating, 2)
    }

# =================== CONTENT SCHEDULING ===================

@apiv1.patch("/content/{content_id}/schedule", response=MessageResponse, auth=apiAuth)
def schedule_content(request, content_id: int, data: ContentScheduleIn):
    """Schedule content release (teacher only)"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not is_teacher_of_course(request.auth, content.course_id):
        raise HttpError(403, "Only teachers can schedule content")
    
    content.scheduled_release = data.scheduled_release
    content.save()
    
    return {"message": "Content scheduled successfully"}

# =================== COURSE ENROLLMENT LIMITS ===================

@apiv1.patch("/courses/{course_id}/enrollment-limit", response=MessageResponse, auth=apiAuth)
def set_enrollment_limit(request, course_id: int, data: EnrollmentLimitIn):
    """Set course enrollment limit (teacher only)"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can set enrollment limits")
    
    course.max_enrollment = data.max_enrollment
    course.save()
    
    return {"message": "Enrollment limit set successfully"}

@apiv1.post("/courses/{course_id}/enroll", response=MessageResponse, auth=apiAuth)
def enroll_in_course(request, course_id: int):
    """Enroll in course with limits checking"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if CourseMember.objects.filter(course_id=course, user_id=request.auth).exists():
        raise HttpError(400, "Already enrolled in this course")
    
    # Check enrollment limit
    if course.max_enrollment:
        current_enrollment = CourseMember.objects.filter(course_id=course).count()
        if current_enrollment >= course.max_enrollment:
            raise HttpError(400, "Course enrollment is full")
    
    CourseMember.objects.create(
        course_id=course,
        user_id=request.auth,
        roles='std'
    )
    
    return {"message": "Successfully enrolled in course"}

# =================== COURSE COMPLETION CERTIFICATES ===================

@apiv1.get("/courses/{course_id}/certificate", response=str, auth=apiAuth)
def get_course_certificate(request, course_id: int):
    """Generate course completion certificate"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_member_of_course(request.auth, course):
        raise HttpError(403, "You must be enrolled in this course")
    
    # Check if user has completed all course content
    total_contents = CourseContent.objects.filter(
        course_id=course, 
        status='published'
    ).count()
    
    completed_contents = ContentCompletion.objects.filter(
        student=request.auth,
        content__course_id=course
    ).count()
    
    if completed_contents < total_contents:
        raise HttpError(400, "Course not completed yet")
    
    # Generate certificate HTML
    certificate_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Course Completion Certificate</title>
        <style>
            body {{ 
                font-family: 'Georgia', serif; 
                text-align: center; 
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
            }}
            .certificate {{
                background: white;
                border: 10px solid #gold;
                border-radius: 20px;
                padding: 60px;
                max-width: 800px;
                margin: 0 auto;
                box-shadow: 0 0 30px rgba(0,0,0,0.3);
            }}
            .header {{ 
                font-size: 48px; 
                color: #2c3e50; 
                margin-bottom: 20px;
                font-weight: bold;
            }}
            .subheader {{ 
                font-size: 24px; 
                color: #7f8c8d; 
                margin-bottom: 40px;
            }}
            .recipient {{ 
                font-size: 36px; 
                color: #2980b9; 
                margin: 30px 0;
                font-weight: bold;
            }}
            .course-title {{ 
                font-size: 28px; 
                color: #27ae60; 
                margin: 20px 0;
                font-style: italic;
            }}
            .completion-date {{ 
                font-size: 18px; 
                color: #95a5a6; 
                margin-top: 40px;
            }}
            .signature {{ 
                margin-top: 60px; 
                font-size: 16px; 
                color: #2c3e50;
            }}
            .ornament {{ 
                font-size: 60px; 
                color: #f1c40f; 
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="certificate">
            <div class="ornament">🏆</div>
            <div class="header">CERTIFICATE OF COMPLETION</div>
            <div class="subheader">This is to certify that</div>
            <div class="recipient">{request.auth.first_name} {request.auth.last_name}</div>
            <div class="subheader">has successfully completed the course</div>
            <div class="course-title">"{course.name}"</div>
            <div class="subheader">with {completed_contents} out of {total_contents} contents completed</div>
            <div class="completion-date">
                Completed on: {timezone.now().strftime('%B %d, %Y')}
            </div>
            <div class="signature">
                <hr style="width: 300px; margin: 40px auto;">
                <strong>{course.teacher.first_name} {course.teacher.last_name}</strong><br>
                Course Instructor
            </div>
            <div class="ornament">✨</div>
        </div>
    </body>
    </html>
    """
    
    return Response(certificate_html, content_type="text/html")

@apiv1.get("/courses/{course_id}/certificate/check", response=CertificateEligibilityOut, auth=apiAuth)
def check_certificate_eligibility(request, course_id: int):
    """Check if user is eligible for certificate"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_member_of_course(request.auth, course):
        raise HttpError(403, "You must be enrolled in this course")
    
    total_contents = CourseContent.objects.filter(
        course_id=course, 
        status='published'
    ).count()
    
    completed_contents = ContentCompletion.objects.filter(
        student=request.auth,
        content__course_id=course
    ).count()
    
    is_eligible = completed_contents >= total_contents and total_contents > 0
    completion_percentage = (completed_contents / total_contents * 100) if total_contents > 0 else 0
    
    return {
        "is_eligible": is_eligible,
        "total_contents": total_contents,
        "completed_contents": completed_contents,
        "completion_percentage": round(completion_percentage, 2)
    }

@apiv1.get("/my-certificates", response=List[UserCertificateOut], auth=apiAuth)
def list_user_certificates(request):
    """List all certificates earned by user"""
    # Get all courses user is enrolled in
    enrolled_courses = Course.objects.filter(coursemember__user_id=request.auth)
    certificates = []
    
    for course in enrolled_courses:
        total_contents = CourseContent.objects.filter(
            course_id=course, 
            status='published'
        ).count()
        
        completed_contents = ContentCompletion.objects.filter(
            student=request.auth,
            content__course_id=course
        ).count()
        
        if completed_contents >= total_contents and total_contents > 0:
            # Get the completion date of the last content
            last_completion = ContentCompletion.objects.filter(
                student=request.auth,
                content__course_id=course
            ).order_by('-completed_at').first()
            
            certificates.append({
                "course_id": course.id,
                "course_name": course.name,
                "course_teacher": f"{course.teacher.first_name} {course.teacher.last_name}",
                "completion_date": last_completion.completed_at if last_completion else timezone.now(),
                "total_contents": total_contents,
                "completed_contents": completed_contents
            })
    
    return certificates