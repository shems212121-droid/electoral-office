"""
Django management command to fix the phone field in Voter model
This avoids migration issues by directly altering the database
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix phone field length in elections_voter table'

    def handle(self, *args, **options):
        self.stdout.write('Starting phone field fix...')
        
        with connection.cursor() as cursor:
            try:
                # Check if we're using PostgreSQL
                self.stdout.write('Checking database type...')
                
                # Drop the unique constraint if it exists
                self.stdout.write('Dropping unique constraint on phone field...')
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM pg_constraint 
                            WHERE conname = 'elections_voter_phone_key'
                        ) THEN
                            ALTER TABLE elections_voter DROP CONSTRAINT elections_voter_phone_key;
                        END IF;
                    END $$;
                """)
                self.stdout.write(self.style.SUCCESS('✓ Unique constraint dropped (if existed)'))
                
                # Alter the column type to VARCHAR(30)
                self.stdout.write('Changing phone field length to 30...')
                cursor.execute("""
                    ALTER TABLE elections_voter 
                    ALTER COLUMN phone TYPE VARCHAR(30);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Phone field length changed to 30'))
                
                # Make sure it's nullable
                self.stdout.write('Ensuring phone field is nullable...')
                cursor.execute("""
                    ALTER TABLE elections_voter 
                    ALTER COLUMN phone DROP NOT NULL;
                """)
                self.stdout.write(self.style.SUCCESS('✓ Phone field set to nullable'))
                
                self.stdout.write(self.style.SUCCESS('\n✅ Phone field fix completed successfully!'))
                self.stdout.write('You can now re-import the missing voter data.')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}'))
                raise
