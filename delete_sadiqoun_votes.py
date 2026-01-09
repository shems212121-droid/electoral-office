import os
import django

# إعداد بيئة جانغو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'electoral_office.settings')
django.setup()

from elections.models import PoliticalParty, VoteCount

def delete_data():
    print("Starting cleanup process...")

    # 1. حذف كتلة الصادقون
    # نبحث عن الاسم بدقة أو جزء منه
    target_parties = PoliticalParty.objects.filter(name__icontains="الصادقون")
    
    if target_parties.exists():
        count = target_parties.count()
        for party in target_parties:
            print(f"Deleting Party: {party.name} (and all its candidates)...")
            party.delete()
        print(f"Successfully deleted {count} party/parties matching 'الصادقون'.")
    else:
        print("No party found matching 'الصادقون'.")

    # 2. حذف جميع أصوات القوائم الحزبية (نتائج الجرد)
    votes_count = VoteCount.objects.count()
    if votes_count > 0:
        print(f"Deleting all {votes_count} vote records (Party List Votes)...")
        VoteCount.objects.all().delete()
        print("All vote records deleted successfully.")
    else:
        print("No vote records found to delete.")

    print("Cleanup completed.")

if __name__ == "__main__":
    delete_data()
