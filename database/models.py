from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """User model for both candidates and recruiters"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'candidate' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    candidate_profile = db.relationship('CandidateProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    recruiter_profile = db.relationship('RecruiterProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CandidateProfile(db.Model):
    """Candidate profile with resume data"""
    __tablename__ = 'candidate_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Basic Info
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))

    # Resume Data (extracted by AI)
    resume_path = db.Column(db.String(255))
    resume_text = db.Column(db.Text)

    # AI-Extracted Fields
    detected_domain = db.Column(db.String(100))  # e.g., "Software Engineering", "Data Science"
    experience_years = db.Column(db.Float, default=0)
    experience_level = db.Column(db.String(50))  # entry, mid, senior
    skills = db.Column(db.Text)  # JSON string of skills
    education = db.Column(db.Text)  # JSON string of education
    work_history = db.Column(db.Text)  # JSON string of work experience

    # Resume Quality Analysis
    resume_score = db.Column(db.Integer, default=0)  # 0-100
    enhancement_suggestions = db.Column(db.Text)  # JSON string

    # Preferences
    preferred_location = db.Column(db.String(100))
    preferred_salary_min = db.Column(db.Integer)
    preferred_salary_max = db.Column(db.Integer)
    preferred_job_type = db.Column(db.String(50))  # fulltime, parttime, contract

    # Embedding for matching (stored as JSON string)
    resume_embedding = db.Column(db.Text)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = db.relationship('Application', backref='candidate', cascade='all, delete-orphan')


class RecruiterProfile(db.Model):
    """Recruiter profile"""
    __tablename__ = 'recruiter_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    full_name = db.Column(db.String(100))
    company_name = db.Column(db.String(200))
    company_description = db.Column(db.Text)
    company_location = db.Column(db.String(100))
    company_website = db.Column(db.String(255))

    # Relationships
    job_postings = db.relationship('JobPosting', backref='recruiter', cascade='all, delete-orphan')


class JobPosting(db.Model):
    """Job postings - both from dataset and recruiter-created"""
    __tablename__ = 'job_postings'

    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter_profiles.id'), nullable=True)

    # Source tracking
    source = db.Column(db.String(50), default='recruiter')  # 'dataset' or 'recruiter'
    original_job_id = db.Column(db.String(50))  # LinkedIn job_id if from dataset

    # Job Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company_name = db.Column(db.String(200))
    company_id = db.Column(db.Integer)  # Links to Company table

    # Location & Work Type
    location = db.Column(db.String(200))
    remote_allowed = db.Column(db.Boolean, default=False)
    work_type = db.Column(db.String(50))  # Fulltime, Parttime, Contract

    # Salary
    min_salary = db.Column(db.Integer)
    max_salary = db.Column(db.Integer)
    med_salary = db.Column(db.Integer)
    pay_period = db.Column(db.String(20))  # Hourly, Monthly, Yearly
    currency = db.Column(db.String(10), default='USD')

    # Requirements
    experience_level = db.Column(db.String(50))  # entry, associate, mid-senior, director, executive
    required_skills = db.Column(db.Text)  # JSON string
    skills_description = db.Column(db.Text)
    qualifications = db.Column(db.Text)

    # Application Info
    application_url = db.Column(db.String(500))
    application_type = db.Column(db.String(50))

    # Metadata
    views = db.Column(db.Integer, default=0)
    applies = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    # AI-Generated Embedding (for matching)
    job_embedding = db.Column(db.Text)

    # Relationships
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan')
    benefits = db.relationship('JobBenefit', backref='job', cascade='all, delete-orphan')


class JobBenefit(db.Model):
    """Benefits associated with job postings"""
    __tablename__ = 'job_benefits'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    benefit_type = db.Column(db.String(100))
    is_inferred = db.Column(db.Boolean, default=False)


class Company(db.Model):
    """Company details from dataset"""
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    original_company_id = db.Column(db.Integer)  # LinkedIn company_id

    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    company_size = db.Column(db.Integer)  # 0-7 scale

    # Location
    country = db.Column(db.String(100))
    state = db.Column(db.String(100))
    city = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))
    address = db.Column(db.String(300))

    # Social
    linkedin_url = db.Column(db.String(300))
    employee_count = db.Column(db.Integer)
    follower_count = db.Column(db.Integer)


class Application(db.Model):
    """Job applications by candidates"""
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_profiles.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)

    # Application Status
    status = db.Column(db.String(50), default='applied')  # applied, reviewed, shortlisted, rejected, hired

    # Match Data
    match_score = db.Column(db.Float)  # Percentage match
    match_reasons = db.Column(db.Text)  # JSON string explaining match

    # Timestamps
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Notes
    candidate_note = db.Column(db.Text)
    recruiter_note = db.Column(db.Text)


class SkillGapAnalysis(db.Model):
    """Stores skill gap analysis results"""
    __tablename__ = 'skill_gap_analyses'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_profiles.id'), nullable=False)

    # Analysis Results
    current_skills = db.Column(db.Text)  # JSON
    missing_skills = db.Column(db.Text)  # JSON
    recommended_skills = db.Column(db.Text)  # JSON

    # Learning Path
    learning_resources = db.Column(db.Text)  # JSON
    career_progression = db.Column(db.Text)  # JSON

    # Target
    target_role = db.Column(db.String(200))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    candidate = db.relationship('CandidateProfile', backref='skill_analyses')


class JobRecommendation(db.Model):
    """Cached job recommendations for candidates"""
    __tablename__ = 'job_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_profiles.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)

    # Match Details
    match_score = db.Column(db.Float)
    match_reasons = db.Column(db.Text)  # JSON

    # Skill Analysis
    matched_skills = db.Column(db.Text)  # JSON
    missing_skills = db.Column(db.Text)  # JSON

    rank = db.Column(db.Integer)  # 1, 2, 3 for top 3

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    candidate = db.relationship('CandidateProfile', backref='recommendations')
    job = db.relationship('JobPosting', backref='recommendations')
