from ninja import NinjaAPI, UploadedFile, File, Form
from ninja.responses import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from lms_core.schema import *
from lms_core.models import *
from lms_core.utils import *
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja.pagination import paginate, PageNumberPagination

apiv1 = NinjaAPI()
apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()

# =================== USER PROFILE MANAGEMENT ===================

@apiv1.post("/register", response=UserRegisterOut)
def register_user(request, data: UserRegisterIn, profile_picture: UploadedFile = File(None)):
    """Register new user with rate limiting"""
    
    # Check rate limiting
    check_registration_rate_limit(request)
    
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
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "message": "Registrasi berhasil"
    }

@apiv1.get("/profile/{user_id}", response=UserFullProfileOut, auth=apiAuth)
def show_profile(request, user_id: int):
    """Show full profile of a user including courses"""
    user = get_object_or_404(User, id=user_id)
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get courses enrolled and created
    courses_enrolled = Course.objects.filter(coursemember__user_id=user)
    courses_created = Course.objects.filter(teacher=user)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile": profile,
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
def create_content(request, course_id: int, data: CourseContentIn, file_attachment: UploadedFile = File(None)):
    """Create course content with rate limiting"""
    course = get_object_or_404(Course, id=course_id)
    
    if not is_teacher_of_course(request.auth, course):
        raise HttpError(403, "Only teachers can create content")
    
    check_content_creation_limit(request.auth)
    
    content_data = {
        'name': data.name,
        'description': data.description,
        'course_id': course,
        'status': data.status or 'draft'
    }
    
    if data.video_url:
        content_data['video_url'] = data.video_url
    
    if file_attachment:
        content_data['file_attachment'] = file_attachment
    
    content = CourseContent.objects.create(**content_data)
    return content

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
    """List content comments"""
    content = get_object_or_404(CourseContent, id=content_id)
    
    if not (is_teacher_of_course(request.auth, content.course_id) or is_member_of_course(request.auth, content.course_id)):
        raise HttpError(403, "Access denied")
    
    if not can_view_content(request.auth, content):
        raise HttpError(403, "Content is not available")
    
    comments = Comment.objects.filter(content_id=content)
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