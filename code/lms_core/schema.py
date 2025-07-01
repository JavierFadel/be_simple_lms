from ninja import Schema
from typing import Optional, List
from datetime import datetime

from django.contrib.auth.models import User

class UserRegisterIn(Schema):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    description: Optional[str]

class UserRegisterOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    message: str

class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str

# Enhanced User Profile Schemas
class UserProfileOut(Schema):
    id: int
    phone_number: Optional[str]
    description: Optional[str]
    profile_picture: Optional[str]

class UserProfileIn(Schema):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    description: Optional[str]

class UserFullProfileOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    profile: Optional[UserProfileOut]
    courses_enrolled: List['CourseSchemaOut']
    courses_created: List['CourseSchemaOut']

# Course Category Schemas
class CourseCategoryOut(Schema):
    id: int
    name: str
    description: Optional[str]
    created_by: UserOut
    created_at: datetime

class CourseCategoryIn(Schema):
    name: str
    description: Optional[str]

# Enhanced Course Schemas
class CourseSchemaOut(Schema):
    id: int
    name: str
    description: str
    price: int
    image: Optional[str]
    teacher: UserOut
    category: Optional[CourseCategoryOut]
    created_at: datetime
    updated_at: datetime

class CourseMemberOut(Schema):
    id: int 
    course_id: CourseSchemaOut
    user_id: UserOut
    roles: str
    created_at: datetime
    updated_at: datetime

class CourseSchemaIn(Schema):
    name: str
    description: str
    price: int
    category_id: Optional[int]
    teacher_id: Optional[int]

# Enhanced Content Schemas
class CourseContentMini(Schema):
    id: int
    name: str
    description: str
    course_id: CourseSchemaOut
    status: str
    created_at: datetime
    updated_at: datetime

class CourseContentFull(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str]
    file_attachment: Optional[str]
    course_id: CourseSchemaOut
    status: str
    created_at: datetime
    updated_at: datetime

# Comment Schemas
class CourseCommentOut(Schema):
    id: int
    content_id: CourseContentMini
    member_id: CourseMemberOut
    comment: str
    created_at: datetime
    updated_at: datetime

class CourseCommentIn(Schema):
    comment: str

class CourseContentIn(Schema):
    name: str
    description: str
    video_url: Optional[str]
    status: Optional[str] = 'draft'

class CourseContentUpdate(Schema):
    name: Optional[str]
    description: Optional[str]
    video_url: Optional[str]
    status: Optional[str]

class CourseAnnouncementOut(Schema):
    id: int
    title: str
    content: str
    course: CourseSchemaOut
    created_by: UserOut
    publish_date: datetime
    created_at: datetime
    updated_at: datetime

class CourseAnnouncementIn(Schema):
    title: str
    content: str
    publish_date: datetime

class CourseAnnouncementUpdate(Schema):
    title: Optional[str]
    content: Optional[str]
    publish_date: Optional[datetime]

# Content Completion Schemas
class ContentCompletionOut(Schema):
    id: int
    student: UserOut
    content: CourseContentMini
    completed_at: datetime

class ContentCompletionIn(Schema):
    content_id: int

# Course Feedback Schemas
class CourseFeedbackOut(Schema):
    id: int
    student: UserOut
    course: CourseSchemaOut
    rating: int
    feedback_text: str
    created_at: datetime
    updated_at: datetime

class CourseFeedbackIn(Schema):
    rating: int
    feedback_text: str

class CourseFeedbackUpdate(Schema):
    rating: Optional[int]
    feedback_text: Optional[str]

# Content Bookmark Schemas
class ContentBookmarkOut(Schema):
    id: int
    student: UserOut
    content: CourseContentFull
    created_at: datetime

class ContentBookmarkIn(Schema):
    content_id: int

# Response Schemas
class MessageResponse(Schema):
    message: str
    status: Optional[str] = "success"

class ErrorResponse(Schema):
    error: str
    detail: Optional[str]

# Statistics Schemas
class CourseStatsOut(Schema):
    total_students: int
    total_contents: int
    total_announcements: int
    completion_rate: float

class UserStatsOut(Schema):
    courses_enrolled: int
    courses_created: int
    contents_completed: int
    bookmarks_count: int