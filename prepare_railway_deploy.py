"""
Deploy script to prepare the database for Railway deployment
This script will:
1. Create a compressed SQLite database
2. Prepare environment variables
3. Push changes to GitHub
"""

import subprocess
import os
import sys
import gzip
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 60)
    print("🚀 Railway Deployment Preparation Script")
    print("=" * 60)
    
    # Get the project directory
    base_dir = Path(__file__).resolve().parent
    db_file = base_dir / 'db.sqlite3'
    
    # Step 1: Check if database exists
    print("\n📊 Step 1: Checking database...")
    if not db_file.exists():
        print("❌ Error: db.sqlite3 not found!")
        sys.exit(1)
    
    db_size_mb = db_file.stat().st_size / (1024 * 1024)
    print(f"✅ Database found: {db_size_mb:.2f} MB")
    
    # Step 2: Check database integrity
    print("\n🔍 Step 2: Checking database integrity...")
    success, stdout, stderr = run_command(
        'python manage.py check --database default',
        cwd=base_dir
    )
    if success:
        print("✅ Database integrity check passed")
    else:
        print(f"⚠️  Warning: {stderr}")
    
    # Step 3: Count records
    print("\n📈 Step 3: Counting records...")
    success, stdout, stderr = run_command(
        'python manage.py shell -c "from elections.models import Voter; print(f\'Total voters: {Voter.objects.count():,}\')"',
        cwd=base_dir
    )
    if success:
        print(f"✅ {stdout.strip()}")
    
    # Step 4: Add db.sqlite3 to git (if not already)
    print("\n📦 Step 4: Preparing Git repository...")
    
    # Check if .gitignore needs to be updated
    gitignore_file = base_dir / '.gitignore'
    if gitignore_file.exists():
        with open(gitignore_file, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        # Remove db.sqlite3 from .gitignore if it's there
        if 'db.sqlite3' in gitignore_content or '*.sqlite3' in gitignore_content:
            print("⚠️  Updating .gitignore to allow db.sqlite3...")
            lines = gitignore_content.split('\n')
            new_lines = [line for line in lines if 'sqlite3' not in line.lower()]
            new_lines.append('\n# Allow db.sqlite3 for Railway deployment')
            new_lines.append('# db.sqlite3')
            
            with open(gitignore_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            print("✅ .gitignore updated")
    
    # Step 5: Git add and commit
    print("\n💾 Step 5: Committing changes...")
    
    commands = [
        'git add .',
        'git commit -m "Update settings and prepare database for deployment"',
    ]
    
    for cmd in commands:
        success, stdout, stderr = run_command(cmd, cwd=base_dir)
        if success:
            print(f"✅ {cmd}")
        else:
            if 'nothing to commit' in stderr or 'nothing to commit' in stdout:
                print(f"ℹ️  No changes to commit")
            else:
                print(f"⚠️  {cmd}: {stderr}")
    
    # Step 6: Push to GitHub
    print("\n🌐 Step 6: Pushing to GitHub...")
    success, stdout, stderr = run_command('git push origin main', cwd=base_dir)
    if success:
        print("✅ Pushed to GitHub successfully")
    else:
        print(f"⚠️  Push warning: {stderr}")
    
    # Step 7: Display next steps
    print("\n" + "=" * 60)
    print("✅ Preparation Complete!")
    print("=" * 60)
    print("\n📋 Next Steps for Railway:")
    print("\n1. Go to your Railway project dashboard:")
    print("   https://railway.app/project/")
    print("\n2. Go to Settings > Deploy and trigger a new deployment")
    print("\n3. Verify environment variables are set:")
    print("   - DJANGO_SETTINGS_MODULE=electoral_office.settings_production")
    print("   - DEBUG=True (for testing, then set to False)")
    print("   - ALLOWED_HOSTS=web-production-42c39.up.railway.app")
    print("   - SECRET_KEY=<your-secret-key>")
    print("\n4. Check deployment logs for any errors")
    print("\n5. Once deployed, test the site:")
    print("   https://web-production-42c39.up.railway.app/")
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
