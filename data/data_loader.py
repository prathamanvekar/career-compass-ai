import os
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_setup import create_app
from database import db
from database.models import JobPosting, Company, JobBenefit


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_data_dir(data_dir: str | os.PathLike) -> Path:
    """Resolve a data directory path.

    If a relative path is provided, it is resolved relative to the project root so
    this script works no matter what the current working directory is.
    """
    candidate = Path(data_dir)
    if candidate.is_absolute():
        return candidate
    return (PROJECT_ROOT / candidate).resolve()

def clean_value(val):
    """Clean pandas value - convert NaN to None"""
    if pd.isna(val):
        return None
    return val

def load_companies(companies_path):
    """Load companies from CSV"""
    print("📊 Loading companies...")

    if not os.path.exists(companies_path):
        print(f"⚠️ Companies file not found: {companies_path}")
        return {}

    df = pd.read_csv(companies_path)
    company_map = {}  # Maps original_company_id to our id

    app = create_app()
    with app.app_context():
        count = 0
        for _, row in df.iterrows():
            try:
                company = Company(
                    original_company_id=clean_value(row.get('company_id')),
                    name=clean_value(row.get('name')),
                    description=clean_value(row.get('description')),
                    company_size=clean_value(row.get('company_size')),
                    country=clean_value(row.get('country')),
                    state=clean_value(row.get('state')),
                    city=clean_value(row.get('city')),
                    zip_code=clean_value(row.get('zip_code')),
                    address=clean_value(row.get('address')),
                    linkedin_url=clean_value(row.get('url'))
                )
                db.session.add(company)
                db.session.flush()

                if row.get('company_id'):
                    company_map[int(row['company_id'])] = company.id

                count += 1
                if count % 1000 == 0:
                    print(f"  Loaded {count} companies...")
                    db.session.commit()

            except Exception as e:
                print(f"  Error loading company: {e}")
                continue

        db.session.commit()
        print(f"✅ Loaded {count} companies")

    return company_map

def extract_skills_from_description(description):
    """Extract skills from job description (basic extraction)"""
    if not description:
        return []

    # Common tech skills to look for
    common_skills = [
        'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker',
        'kubernetes', 'react', 'angular', 'node.js', 'machine learning',
        'data analysis', 'excel', 'powerpoint', 'communication', 'leadership',
        'project management', 'agile', 'scrum', 'git', 'linux', 'html', 'css',
        'tensorflow', 'pytorch', 'tableau', 'power bi', 'salesforce', 'sap',
        'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust', 'scala', 'r',
        'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
        'spark', 'hadoop', 'kafka', 'airflow', 'jenkins', 'ci/cd'
    ]

    description_lower = description.lower()
    found_skills = [skill for skill in common_skills if skill in description_lower]

    return found_skills

def load_job_postings(jobs_path, company_map, limit=None):
    """Load job postings from CSV"""
    print("📊 Loading job postings...")

    if not os.path.exists(jobs_path):
        print(f"⚠️ Jobs file not found: {jobs_path}")
        return

    df = pd.read_csv(jobs_path)

    if limit:
        df = df.head(limit)

    app = create_app()
    with app.app_context():
        count = 0
        for _, row in df.iterrows():
            try:
                # Extract skills from description
                skills = extract_skills_from_description(clean_value(row.get('description')))

                # Also check skills_desc column
                skills_desc = clean_value(row.get('skills_desc'))
                if skills_desc:
                    skills_from_desc = [s.strip() for s in skills_desc.split(',')]
                    skills = list(set(skills + skills_from_desc))

                # Get company name
                company_id = clean_value(row.get('company_id'))
                company_name = None
                if company_id and int(company_id) in company_map:
                    company = db.session.get(Company, company_map[int(company_id)])
                    if company:
                        company_name = company.name

                job = JobPosting(
                    source='dataset',
                    original_job_id=str(clean_value(row.get('job_id'))),
                    title=clean_value(row.get('title')) or 'Untitled Position',
                    description=clean_value(row.get('description')) or '',
                    company_name=company_name,
                    company_id=company_map.get(int(company_id)) if company_id else None,
                    location=clean_value(row.get('location')),
                    remote_allowed=bool(clean_value(row.get('remote_allowed'))),
                    work_type=clean_value(row.get('formatted_work_type')),
                    min_salary=clean_value(row.get('min_salary')),
                    max_salary=clean_value(row.get('max_salary')),
                    med_salary=clean_value(row.get('med_salary')),
                    pay_period=clean_value(row.get('pay_period')),
                    currency=clean_value(row.get('currency')) or 'USD',
                    experience_level=clean_value(row.get('formatted_experience_level')),
                    required_skills=json.dumps(skills) if skills else None,
                    skills_description=skills_desc,
                    application_url=clean_value(row.get('application_url')),
                    application_type=clean_value(row.get('application_type')),
                    views=clean_value(row.get('views')) or 0,
                    applies=clean_value(row.get('applies')) or 0,
                    is_active=True
                )

                db.session.add(job)
                count += 1

                if count % 1000 == 0:
                    print(f"  Loaded {count} jobs...")
                    db.session.commit()

            except Exception as e:
                print(f"  Error loading job: {e}")
                continue

        db.session.commit()
        print(f"✅ Loaded {count} job postings")

def load_benefits(benefits_path):
    """Load job benefits from CSV"""
    print("📊 Loading benefits...")

    if not os.path.exists(benefits_path):
        print(f"⚠️ Benefits file not found: {benefits_path}")
        return

    df = pd.read_csv(benefits_path)

    app = create_app()
    with app.app_context():
        # Get job ID mapping
        jobs = JobPosting.query.filter_by(source='dataset').all()
        job_map = {job.original_job_id: job.id for job in jobs}

        count = 0
        for _, row in df.iterrows():
            try:
                original_job_id = str(clean_value(row.get('job_id')))
                if original_job_id not in job_map:
                    continue

                benefit = JobBenefit(
                    job_id=job_map[original_job_id],
                    benefit_type=clean_value(row.get('type')),
                    is_inferred=bool(clean_value(row.get('inferred')))
                )
                db.session.add(benefit)
                count += 1

                if count % 5000 == 0:
                    print(f"  Loaded {count} benefits...")
                    db.session.commit()

            except Exception as e:
                continue

        db.session.commit()
        print(f"✅ Loaded {count} benefits")

def load_all_data(data_dir='data', job_limit=10000):
    """Load all data from CSV files"""
    print("\n" + "="*50)
    print("🚀 Starting Data Load Process")
    print("="*50 + "\n")

    # Paths (resolve relative to project root, not the current working dir)
    resolved_data_dir = _resolve_data_dir(data_dir)
    companies_path = resolved_data_dir / 'companies.csv'
    jobs_path = resolved_data_dir / 'job_postings.csv'
    benefits_path = resolved_data_dir / 'benefits.csv'

    # Load companies first
    company_map = load_companies(str(companies_path))

    # Load jobs (with limit for faster loading)
    load_job_postings(str(jobs_path), company_map, limit=job_limit)

    # Load benefits
    load_benefits(str(benefits_path))

    print("\n" + "="*50)
    print("✅ Data Load Complete!")
    print("="*50)

    # Print summary
    app = create_app()
    with app.app_context():
        print(f"\n📊 Database Summary:")
        print(f"  - Companies: {Company.query.count()}")
        print(f"  - Job Postings: {JobPosting.query.count()}")
        print(f"  - Benefits: {JobBenefit.query.count()}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Load CSV seed data into the database')
    parser.add_argument('--data-dir', default='data', help='Directory containing CSV files (default: data)')
    parser.add_argument('--job-limit', type=int, default=10000, help='Max number of jobs to load (default: 10000)')
    args = parser.parse_args()

    # First, initialize the database
    from database.db_setup import init_database
    init_database()

    # Then load data
    load_all_data(data_dir=args.data_dir, job_limit=args.job_limit)
