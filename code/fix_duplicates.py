
from lms_core.models import CourseMember
from collections import defaultdict

# Handle duplicates in CourseMember table
def clean_duplicates():
    duplicates = defaultdict(list)

    for cm in CourseMember.objects.all():
        key = (cm.course_id_id, cm.user_id_id)
        duplicates[key].append(cm.id)

    found = False
    for key, ids in duplicates.items():
        if len(ids) > 1:
            print(f"Duplikat ditemukan untuk {key}: {ids}")
            CourseMember.objects.filter(id__in=ids[1:]).delete()
            print(f"-> {len(ids) - 1} duplikat dihapus.")
            found = True

    if not found:
        print("Tidak ada duplikat ditemukan.")

if __name__ == "__main__":
    clean_duplicates()
