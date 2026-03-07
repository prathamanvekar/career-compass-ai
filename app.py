import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from database import db
from database.models import (
    User, CandidateProfile, RecruiterProfile,
    JobPosting, Application, JobRecommendation, SkillGapAnalysis
)

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_recruiter_jobs_query():
    """Get query for only recruiter-posted jobs"""
    return JobPosting.query.filter_by(is_active=True, source='recruiter')


def get_active_recruiter_jobs():
    """Get all active jobs posted by recruiters only"""
    return get_recruiter_jobs_query().all()


def get_recruiter_jobs_count():
    """Get count of active recruiter-posted jobs"""
    return get_recruiter_jobs_query().count()


# ============================================
# PUBLIC ROUTES
# ============================================

@app.route('/')
def index():
    """Landing page"""
    # Only count jobs posted by recruiters
    job_count = get_recruiter_jobs_count()
    return render_template('index.html', job_count=job_count)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'candidate')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))

        # Create user
        user = User(email=email, user_type=user_type)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create profile based on type
        if user_type == 'candidate':
            profile = CandidateProfile(user_id=user.id)
            db.session.add(profile)
        else:
            profile = RecruiterProfile(user_id=user.id)
            db.session.add(profile)

        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

        flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect to appropriate dashboard"""
    if current_user.user_type == 'candidate':
        return redirect(url_for('candidate_dashboard'))
    else:
        return redirect(url_for('recruiter_dashboard'))


# ============================================
# CANDIDATE ROUTES
# ============================================

@app.route('/candidate/dashboard')
@login_required
def candidate_dashboard():
    """Candidate main dashboard"""
    if current_user.user_type != 'candidate':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile

    # Get stats
    applications_count = Application.query.filter_by(candidate_id=profile.id).count()
    recommendations = JobRecommendation.query.filter_by(candidate_id=profile.id).order_by(JobRecommendation.rank).limit(3).all()

    # Get count of available recruiter jobs
    available_jobs_count = get_recruiter_jobs_count()

    return render_template('candidate/dashboard.html',
                          profile=profile,
                          applications_count=applications_count,
                          recommendations=recommendations,
                          available_jobs_count=available_jobs_count)


@app.route('/candidate/upload-resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    """Upload and analyze resume"""
    if current_user.user_type != 'candidate':
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['resume']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Parse resume using AI
            from ai_engine.resume_parser import ResumeParser
            parser = ResumeParser()

            try:
                # Extract text
                resume_text = parser.extract_text(filepath)

                if not resume_text:
                    flash('Could not extract text from resume', 'error')
                    return redirect(request.url)

                # Parse with AI
                parsed_data = parser.parse_resume(resume_text)

                if not parsed_data:
                    flash('Could not parse resume. Please try again.', 'error')
                    return redirect(request.url)

                # Analyze quality
                quality_analysis = parser.analyze_resume_quality(resume_text, parsed_data)

                # Update profile
                profile.resume_path = filepath
                profile.resume_text = resume_text
                profile.full_name = parsed_data.get('full_name') or profile.full_name
                profile.phone = parsed_data.get('phone')
                profile.location = parsed_data.get('location')
                profile.detected_domain = parsed_data.get('detected_domain')
                profile.experience_years = parsed_data.get('experience_years', 0)
                profile.experience_level = parsed_data.get('experience_level')
                profile.skills = json.dumps(parsed_data.get('skills', []))
                profile.education = json.dumps(parsed_data.get('education', []))
                profile.work_history = json.dumps(parsed_data.get('work_history', []))
                profile.resume_score = quality_analysis.get('overall_score', 0)
                profile.enhancement_suggestions = json.dumps(quality_analysis)

                db.session.commit()

                # Generate job recommendations (only from recruiter jobs)
                try:
                    generate_recommendations(profile.id)
                except Exception as rec_error:
                    print(f"Error generating recommendations: {rec_error}")

                flash('Resume uploaded and analyzed successfully!', 'success')
                return redirect(url_for('resume_analysis'))

            except Exception as e:
                print(f"Error processing resume: {e}")
                flash(f'Error processing resume: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload PDF or DOCX.', 'error')

    return render_template('candidate/upload_resume.html', profile=profile)


@app.route('/candidate/resume-analysis')
@login_required
def resume_analysis():
    """View resume analysis results"""
    if current_user.user_type != 'candidate':
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile

    # Parse JSON fields safely
    try:
        skills = json.loads(profile.skills) if profile.skills else []
    except:
        skills = []

    try:
        education = json.loads(profile.education) if profile.education else []
    except:
        education = []

    try:
        work_history = json.loads(profile.work_history) if profile.work_history else []
    except:
        work_history = []

    try:
        enhancement = json.loads(profile.enhancement_suggestions) if profile.enhancement_suggestions else {}
    except:
        enhancement = {}

    return render_template('candidate/resume_analysis.html',
                          profile=profile,
                          skills=skills,
                          education=education,
                          work_history=work_history,
                          enhancement=enhancement)


@app.route('/candidate/job-recommendations')
@login_required
def job_recommendations():
    """View job recommendations"""
    if current_user.user_type != 'candidate':
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile

    # Get recommendations
    recommendations = JobRecommendation.query.filter_by(
        candidate_id=profile.id
    ).order_by(JobRecommendation.rank).all()

    # Enrich with job details (only include if job still exists and is from recruiter)
    enriched_recs = []
    for rec in recommendations:
        job = db.session.get(JobPosting, rec.job_id)
        # Only include recruiter-posted jobs
        if job and job.source == 'recruiter' and job.is_active:
            try:
                reasons = json.loads(rec.match_reasons) if rec.match_reasons else []
            except:
                reasons = []
            try:
                matched_skills = json.loads(rec.matched_skills) if rec.matched_skills else []
            except:
                matched_skills = []
            try:
                missing_skills = json.loads(rec.missing_skills) if rec.missing_skills else []
            except:
                missing_skills = []

            enriched_recs.append({
                'recommendation': rec,
                'job': job,
                'match_score': rec.match_score,
                'reasons': reasons,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills
            })

    # Check if there are any recruiter jobs available
    available_jobs_count = get_recruiter_jobs_count()

    return render_template('candidate/job_recommendations.html',
                          recommendations=enriched_recs,
                          profile=profile,
                          available_jobs_count=available_jobs_count)


@app.route('/candidate/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_to_job(job_id):
    """Apply to a job"""
    if current_user.user_type != 'candidate':
        return jsonify({'error': 'Unauthorized'}), 403

    profile = current_user.candidate_profile
    job = db.session.get(JobPosting, job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Only allow applying to recruiter-posted jobs
    if job.source != 'recruiter':
        return jsonify({'error': 'This job is not available for applications'}), 400

    # Check if already applied
    existing = Application.query.filter_by(
        candidate_id=profile.id,
        job_id=job_id
    ).first()

    if existing:
        return jsonify({'error': 'Already applied to this job'}), 400

    # Get recommendation for match score
    rec = JobRecommendation.query.filter_by(
        candidate_id=profile.id,
        job_id=job_id
    ).first()

    application = Application(
        candidate_id=profile.id,
        job_id=job_id,
        status='applied',
        match_score=rec.match_score if rec else None,
        match_reasons=rec.match_reasons if rec else None
    )

    db.session.add(application)
    job.applies = (job.applies or 0) + 1
    db.session.commit()

    return jsonify({'success': True, 'message': 'Application submitted!'})


@app.route('/candidate/applications')
@login_required
def my_applications():
    """View applied jobs"""
    if current_user.user_type != 'candidate':
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile
    applications = Application.query.filter_by(candidate_id=profile.id).order_by(Application.applied_at.desc()).all()

    return render_template('candidate/applications.html', applications=applications)


@app.route('/candidate/career-map')
@login_required
def career_map():
    """View career progression map"""
    if current_user.user_type != 'candidate':
        return redirect(url_for('dashboard'))

    profile = current_user.candidate_profile

    # Check if resume is uploaded
    if not profile.resume_path:
        flash('Please upload your resume first to view career map.', 'warning')
        return redirect(url_for('upload_resume'))

    # Get or generate skill analysis
    analysis = SkillGapAnalysis.query.filter_by(candidate_id=profile.id).order_by(SkillGapAnalysis.created_at.desc()).first()

    if not analysis:
        try:
            # Generate new analysis
            from ai_engine.skill_analyzer import SkillAnalyzer
            analyzer = SkillAnalyzer()

            # Get target jobs for skill comparison (only recruiter jobs)
            recommendations = JobRecommendation.query.filter_by(candidate_id=profile.id).all()
            target_skills = set()
            for rec in recommendations:
                job = db.session.get(JobPosting, rec.job_id)
                if job and job.source == 'recruiter' and job.required_skills:
                    try:
                        skills = json.loads(job.required_skills)
                        target_skills.update(skills)
                    except:
                        pass

            # Perform analysis
            try:
                candidate_skills = json.loads(profile.skills) if profile.skills else []
            except:
                candidate_skills = []

            gap_result = analyzer.analyze_skill_gap(candidate_skills, list(target_skills))

            # Get learning path
            learning_path = {}
            if gap_result['missing_skills']:
                learning_path = analyzer.get_learning_path(
                    gap_result['missing_skills'][:10],
                    current_domain=profile.detected_domain
                )

            # Get career progression
            profile_dict = {
                'skills': candidate_skills,
                'detected_domain': profile.detected_domain,
                'experience_level': profile.experience_level,
                'experience_years': profile.experience_years
            }
            career_progression = analyzer.get_career_progression(profile_dict)

            # Save analysis
            analysis = SkillGapAnalysis(
                candidate_id=profile.id,
                current_skills=json.dumps(candidate_skills),
                missing_skills=json.dumps(gap_result['missing_skills']),
                recommended_skills=json.dumps(gap_result.get('extra_skills', [])),
                learning_resources=json.dumps(learning_path),
                career_progression=json.dumps(career_progression)
            )
            db.session.add(analysis)
            db.session.commit()

        except Exception as e:
            print(f"Error generating career map: {e}")
            try:
                candidate_skills = json.loads(profile.skills) if profile.skills else []
            except:
                candidate_skills = []

            return render_template('candidate/career_map.html',
                              profile=profile,
                              current_skills=candidate_skills,
                              missing_skills=[],
                              learning_path={},
                              career_progression={},
                              error_message="Could not generate full career analysis. Please try again later.")

    # Parse stored JSON safely
    try:
        current_skills = json.loads(analysis.current_skills) if analysis.current_skills else []
    except:
        current_skills = []

    try:
        missing_skills = json.loads(analysis.missing_skills) if analysis.missing_skills else []
    except:
        missing_skills = []

    try:
        learning_path = json.loads(analysis.learning_resources) if analysis.learning_resources else {}
    except:
        learning_path = {}

    try:
        career_progression = json.loads(analysis.career_progression) if analysis.career_progression else {}
    except:
        career_progression = {}

    return render_template('candidate/career_map.html',
                          profile=profile,
                          current_skills=current_skills,
                          missing_skills=missing_skills,
                          learning_path=learning_path,
                          career_progression=career_progression)


# ============================================
# RECRUITER ROUTES
# ============================================

@app.route('/recruiter/dashboard')
@login_required
def recruiter_dashboard():
    """Recruiter main dashboard"""
    if current_user.user_type != 'recruiter':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))

    profile = current_user.recruiter_profile

    # Only get jobs posted by this recruiter
    jobs = JobPosting.query.filter_by(
        recruiter_id=profile.id,
        source='recruiter'
    ).order_by(JobPosting.created_at.desc()).all()

    # Stats
    total_jobs = len(jobs)
    total_applications = sum(j.applies or 0 for j in jobs)
    active_jobs = len([j for j in jobs if j.is_active])

    return render_template('recruiter/dashboard.html',
                          profile=profile,
                          jobs=jobs,
                          total_jobs=total_jobs,
                          total_applications=total_applications,
                          active_jobs=active_jobs)


@app.route('/recruiter/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    """Post a new job"""
    if current_user.user_type != 'recruiter':
        return redirect(url_for('dashboard'))

    profile = current_user.recruiter_profile

    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        work_type = request.form.get('work_type')
        experience_level = request.form.get('experience_level')
        min_salary = request.form.get('min_salary')
        max_salary = request.form.get('max_salary')
        skills = request.form.get('skills', '').split(',')
        remote_allowed = request.form.get('remote_allowed') == 'on'

        # Clean skills
        skills = [s.strip() for s in skills if s.strip()]

        # Create job posting (source='recruiter' is important!)
        job = JobPosting(
            recruiter_id=profile.id,
            source='recruiter',  # This marks it as a recruiter-posted job
            title=title,
            description=description,
            company_name=profile.company_name,
            location=location,
            work_type=work_type,
            experience_level=experience_level,
            min_salary=int(min_salary) if min_salary else None,
            max_salary=int(max_salary) if max_salary else None,
            required_skills=json.dumps(skills),
            remote_allowed=remote_allowed,
            is_active=True
        )

        db.session.add(job)
        db.session.commit()

        flash('Job posted successfully! Candidates can now see and apply to this job.', 'success')
        return redirect(url_for('recruiter_dashboard'))

    return render_template('recruiter/post_job.html', profile=profile)


@app.route('/recruiter/job/<int:job_id>')
@login_required
def view_job_applications(job_id):
    """View applications for a job"""
    if current_user.user_type != 'recruiter':
        return redirect(url_for('dashboard'))

    job = db.session.get(JobPosting, job_id)

    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('recruiter_dashboard'))

    # Verify ownership
    if job.recruiter_id != current_user.recruiter_profile.id:
        flash('Access denied', 'error')
        return redirect(url_for('recruiter_dashboard'))

    applications = Application.query.filter_by(job_id=job_id).order_by(Application.match_score.desc()).all()

    return render_template('recruiter/view_applications.html',
                          job=job,
                          applications=applications)


@app.route('/recruiter/job/<int:job_id>/toggle', methods=['POST'])
@login_required
def toggle_job_status(job_id):
    """Toggle job active/inactive status"""
    if current_user.user_type != 'recruiter':
        return jsonify({'error': 'Unauthorized'}), 403

    job = db.session.get(JobPosting, job_id)

    if not job or job.recruiter_id != current_user.recruiter_profile.id:
        return jsonify({'error': 'Job not found'}), 404

    job.is_active = not job.is_active
    db.session.commit()

    status = 'activated' if job.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Job {status}', 'is_active': job.is_active})


@app.route('/recruiter/profile', methods=['GET', 'POST'])
@login_required
def recruiter_profile():
    """Update recruiter profile"""
    if current_user.user_type != 'recruiter':
        return redirect(url_for('dashboard'))

    profile = current_user.recruiter_profile

    if request.method == 'POST':
        profile.full_name = request.form.get('full_name')
        profile.company_name = request.form.get('company_name')
        profile.company_description = request.form.get('company_description')
        profile.company_location = request.form.get('company_location')
        profile.company_website = request.form.get('company_website')

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('recruiter_dashboard'))

    return render_template('recruiter/profile.html', profile=profile)


# ============================================
# JOB BROWSING (PUBLIC - Only Recruiter Jobs)
# ============================================

@app.route('/jobs')
def browse_jobs():
    """Browse all active jobs (ONLY recruiter-posted jobs)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Filters
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    work_type = request.args.get('work_type', '')
    experience = request.args.get('experience', '')

    # Build query - ONLY recruiter jobs
    query = JobPosting.query.filter_by(is_active=True, source='recruiter')

    if search:
        query = query.filter(
            JobPosting.title.contains(search) |
            JobPosting.description.contains(search)
        )
    if location:
        query = query.filter(JobPosting.location.contains(location))
    if work_type:
        query = query.filter(JobPosting.work_type == work_type)
    if experience:
        query = query.filter(JobPosting.experience_level == experience)

    jobs = query.order_by(JobPosting.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('jobs.html', jobs=jobs, search=search,
                          location=location, work_type=work_type, experience=experience)


@app.route('/job/<int:job_id>')
def view_job(job_id):
    """View job details"""
    job = db.session.get(JobPosting, job_id)

    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('browse_jobs'))

    # Only allow viewing recruiter-posted jobs publicly
    if job.source != 'recruiter':
        flash('This job is not available', 'error')
        return redirect(url_for('browse_jobs'))

    job.views = (job.views or 0) + 1
    db.session.commit()

    try:
        skills = json.loads(job.required_skills) if job.required_skills else []
    except:
        skills = []

    benefits = job.benefits

    # Check if candidate has applied
    applied = False
    if current_user.is_authenticated and current_user.user_type == 'candidate':
        applied = Application.query.filter_by(
            candidate_id=current_user.candidate_profile.id,
            job_id=job_id
        ).first() is not None

    return render_template('job_detail.html', job=job, skills=skills,
                          benefits=benefits, applied=applied)


# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_recommendations(candidate_id):
    """Generate job recommendations for a candidate (ONLY from recruiter jobs)"""
    from ai_engine.job_matcher import JobMatcher

    profile = db.session.get(CandidateProfile, candidate_id)
    if not profile:
        return

    # Clear old recommendations
    JobRecommendation.query.filter_by(candidate_id=candidate_id).delete()

    # Get ONLY active recruiter-posted jobs
    jobs = JobPosting.query.filter_by(
        is_active=True,
        source='recruiter'  # IMPORTANT: Only recruiter jobs!
    ).all()

    if not jobs:
        print("No recruiter jobs available for recommendations")
        db.session.commit()
        return

    # Prepare profile dict
    try:
        skills = json.loads(profile.skills) if profile.skills else []
    except:
        skills = []

    profile_dict = {
        'skills': skills,
        'detected_domain': profile.detected_domain,
        'experience_level': profile.experience_level,
        'experience_years': profile.experience_years,
        'preferred_location': profile.preferred_location,
        'preferred_salary_min': profile.preferred_salary_min,
        'preferred_salary_max': profile.preferred_salary_max,
        'location': profile.location
    }

    # Prepare jobs list
    jobs_list = []
    for job in jobs:
        jobs_list.append({
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'required_skills': job.required_skills,
            'skills_description': job.skills_description,
            'experience_level': job.experience_level,
            'location': job.location,
            'remote_allowed': job.remote_allowed,
            'min_salary': job.min_salary,
            'max_salary': job.max_salary
        })

    # Get matches
    matcher = JobMatcher()

    # Get ALL matches first, then take top ones
    all_matches = matcher.find_top_matches(
        profile_dict,
        jobs_list,
        top_n=len(jobs_list)  # Get all matches
    )

    # Ensure at least ALWAYS_SHOW_MIN_JOBS are shown
    min_jobs = getattr(Config, 'ALWAYS_SHOW_MIN_JOBS', 1)

    # If we have fewer matches than minimum, include all available jobs
    if len(all_matches) < min_jobs and jobs_list:
        # Add remaining jobs that weren't matched
        matched_ids = {m['job']['id'] for m in all_matches}
        for job_data in jobs_list:
            if job_data['id'] not in matched_ids and len(all_matches) < min_jobs:
                all_matches.append({
                    'job': job_data,
                    'match_score': 10.0,  # Low default score
                    'reasons': ['Available position in your area of interest'],
                    'detailed_scores': {}
                })

    # Take top 3 (or configured amount)
    top_matches = all_matches[:Config.TOP_JOBS_COUNT]

    # Save recommendations
    for rank, match in enumerate(top_matches, 1):
        job_data = match['job']

        # Calculate matched/missing skills
        candidate_skills = set(s.lower() for s in profile_dict['skills'] if s)
        job_skills = job_data.get('required_skills', [])
        if isinstance(job_skills, str):
            try:
                job_skills = json.loads(job_skills) if job_skills else []
            except:
                job_skills = []
        job_skills_set = set(s.lower() for s in job_skills if s)

        matched = list(candidate_skills & job_skills_set)
        missing = list(job_skills_set - candidate_skills)

        rec = JobRecommendation(
            candidate_id=candidate_id,
            job_id=job_data['id'],
            match_score=match['match_score'],
            match_reasons=json.dumps(match['reasons']),
            matched_skills=json.dumps(matched),
            missing_skills=json.dumps(missing),
            rank=rank
        )
        db.session.add(rec)

    db.session.commit()
    print(f"Generated {len(top_matches)} recommendations from {len(jobs)} recruiter jobs")


# ============================================
# API ROUTES (for AJAX calls)
# ============================================

@app.route('/api/refresh-recommendations', methods=['POST'])
@login_required
def refresh_recommendations():
    """Regenerate job recommendations"""
    if current_user.user_type != 'candidate':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        generate_recommendations(current_user.candidate_profile.id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    """Update candidate job preferences"""
    if current_user.user_type != 'candidate':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    profile = current_user.candidate_profile

    profile.preferred_location = data.get('location')
    profile.preferred_salary_min = data.get('salary_min')
    profile.preferred_salary_max = data.get('salary_max')
    profile.preferred_job_type = data.get('job_type')

    db.session.commit()

    # Regenerate recommendations with new preferences
    try:
        generate_recommendations(profile.id)
    except Exception as e:
        print(f"Error regenerating recommendations: {e}")

    return jsonify({'success': True})


@app.route('/api/jobs/count')
def get_jobs_count():
    """Get count of available recruiter jobs"""
    count = get_recruiter_jobs_count()
    return jsonify({'count': count})


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
