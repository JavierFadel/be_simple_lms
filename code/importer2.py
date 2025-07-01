import os
import sys
sys.path.append(os.path.abspath(os.path.join(__file__, *[os.pardir] * 3)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'simplelms.settings'
import django
django.setup()

import csv
import json
from random import randint
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from lms_core.models import Course, CourseMember, CourseContent, Comment

import time
start_time = time.time()

filepath = './csv_data/'

with open(filepath+'user-data.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        obj_create = []
        for num, row in enumerate(reader):
            if not User.objects.filter(username=row['username']).exists():
                obj_create.append(User(username=row['username'], 
                                         password=make_password(row['password']), 
                                         email=row['email'],
                                         first_name=row['firstname'],
                                         last_name=row['lastname']))
        User.objects.bulk_create(obj_create)


with open(filepath+'course-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    obj_create = []
    for num,row in enumerate(reader):
        if not Course.objects.filter(pk=num+1).exists():
            obj_create.append(Course(name=row['name'], price=row['price'],
                                  description=row['description'], 
                                  teacher=User.objects.get(pk=int(row['teacher']))))
    Course.objects.bulk_create(obj_create)


with open(filepath+'member-data.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    obj_create = []
    existing_pairs = set(CourseMember.objects.values_list('course_id_id', 'user_id_id'))

    for row in reader:
        course_id = int(row['course_id'])
        user_id = int(row['user_id'])
        roles = row['roles']

        if (course_id, user_id) not in existing_pairs:
            course = Course.objects.get(pk=course_id)
            user = User.objects.get(pk=user_id)
            obj_create.append(CourseMember(course_id=course, user_id=user, roles=roles))
            existing_pairs.add((course_id, user_id))

    CourseMember.objects.bulk_create(obj_create)


with open(filepath+'contents.json') as jsonfile:
    comments = json.load(jsonfile)
    obj_create = []
    for num, row in enumerate(comments):
        if not CourseContent.objects.filter(pk=num+1).exists():
            obj_create.append(CourseContent(course_id=Course.objects.get(pk=int(row['course_id'])), 
                                         video_url=row['video_url'], name=row['name'], 
                                         description=row['description']))
    CourseContent.objects.bulk_create(obj_create)


with open(filepath+'comments.json') as jsonfile:
    comments = json.load(jsonfile)
    obj_create = []

    for row in comments:
        if int(row['user_id']) > 50:
            row['user_id'] = randint(5, 40)

        try:
            user_id = int(row.get('user_id')) if row.get('user_id') else None
            content_id = int(row.get('content_id')) if row.get('content_id') else None

            if user_id and content_id:
                content = CourseContent.objects.get(pk=content_id)
                course_id = content.course_id_id

                course_member = CourseMember.objects.get(user_id__id=user_id, course_id__id=course_id)
                obj_create.append(Comment(content_id=content, member_id=course_member, comment=row['comment']))
            else:
                print(f"Skip: Missing user_id/content_id in row: {row}")
        except CourseContent.DoesNotExist:
            print(f"Skip: CourseContent not found for content_id={row.get('content_id')}")
        except CourseMember.DoesNotExist:
            print(f"Skip: CourseMember not found for user_id={row.get('user_id')} and course_id inferred from content_id")


    Comment.objects.bulk_create(obj_create)

print("--- %s seconds ---" % (time.time() - start_time))