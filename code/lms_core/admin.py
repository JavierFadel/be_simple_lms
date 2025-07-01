from django.contrib import admin
from lms_core.models import *
from lms_core.models import UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('phone_number', 'description', 'profile_picture')

# Enhanced User Admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone')
    
    def get_phone(self, obj):
        try:
            return obj.profile.phone_number
        except:
            return '-'
    get_phone.short_description = 'Phone Number'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Course Category Admin
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    list_filter = ('created_at', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

# Enhanced Course Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'category', 'price', 'created_at')
    list_filter = ('category', 'teacher', 'created_at')
    search_fields = ('name', 'description', 'teacher__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('teacher',)

@admin.register(CourseMember)
class CourseMemberAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'user_id', 'roles', 'created_at')
    list_filter = ('roles', 'created_at')
    search_fields = ('course_id__name', 'user_id__username')
    raw_id_fields = ('course_id', 'user_id')

# Enhanced Content Admin
@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_id', 'status', 'created_at')
    list_filter = ('status', 'course_id', 'created_at')
    search_fields = ('name', 'description', 'course_id__name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('course_id', 'parent_id')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('get_content', 'get_user', 'comment_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'content_id__name', 'member_id__user_id__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('content_id', 'member_id')
    
    def get_content(self, obj):
        return obj.content_id.name
    get_content.short_description = 'Content'
    
    def get_user(self, obj):
        return obj.member_id.user_id.username
    get_user.short_description = 'User'
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment Preview'

@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'created_by', 'publish_date', 'created_at')
    list_filter = ('course', 'created_by', 'publish_date')
    search_fields = ('title', 'content', 'course__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ContentCompletion)
class ContentCompletionAdmin(admin.ModelAdmin):
    list_display = ('student', 'content', 'completed_at')
    list_filter = ('student', 'content')
    search_fields = ('student__username', 'content__name')

@admin.register(CourseFeedback)
class CourseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at')
    list_filter = ('course', 'rating', 'created_at')
    search_fields = ('student__username', 'course__name', 'feedback_text')

@admin.register(ContentBookmark)
class ContentBookmarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'content', 'created_at')
    list_filter = ('student', 'content')
    search_fields = ('student__username', 'content__name')

@admin.register(RegistrationAttempt)
class RegistrationAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'attempted_at')
    list_filter = ('ip_address',)
    search_fields = ('ip_address',)

@admin.register(CommentRateLimit)
class CommentRateLimitAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment_count', 'hour_started')
    list_filter = ('user',)
    search_fields = ('user__username',)

@admin.register(CourseCreationLimit)
class CourseCreationLimitAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'courses_created', 'date_created')
    list_filter = ('teacher', 'date_created')
    search_fields = ('teacher__username',)

@admin.register(ContentCreationLimit)
class ContentCreationLimitAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'content_count', 'hour_started')
    list_filter = ('teacher',)
    search_fields = ('teacher__username',)