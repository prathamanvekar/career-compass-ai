# Job Portal Setup Guide

This guide will help you set up and run the AI-powered Job Portal from scratch.

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher** installed
- **pip** (Python package manager)
- **Virtual environment** tool (recommended)
- A **Groq API key** (free from https://console.groq.com/)

---

## 🚀 Step-by-Step Setup

### Step 1: Create Virtual Environment

```bash
# Navigate to the project directory
cd job_portal

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

---

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**What this installs:**

- Flask (web framework)
- SQLAlchemy (database)
- AI/ML libraries (sentence-transformers, scikit-learn, pandas, numpy)
- Document processing (PyPDF2, python-docx, pdfplumber)
- Groq API client
- Other utilities

**Note:** First installation may take 5-10 minutes as it downloads ML models (~90MB for sentence-transformers).

---

### Step 3: Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# Create .env file
touch .env  # On Linux/Mac
type nul > .env  # On Windows
```

Add the following to your `.env` file:

```env
# Flask Secret Key (change this to a random string in production)
SECRET_KEY=your-super-secret-key-12345

# Groq API Key (get free key from https://console.groq.com/)
GROQ_API_KEY=your_groq_api_key_here
```

**Getting your Groq API Key:**

1. Go to https://console.groq.com/
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into your `.env` file

---

### Step 4: Initialize the Database

Run the database setup script to create all necessary tables:

```bash
python database/db_setup.py
```

**What this does:**

- Creates a SQLite database at `database/job_portal.db`
- Creates all tables:
  - `user` (authentication)
  - `candidate_profile` (candidate data)
  - `recruiter_profile` (recruiter data)
  - `job_posting` (job listings)
  - `application` (job applications)
  - `job_recommendation` (AI-generated matches)
  - `skill_gap_analysis` (career analysis)
  - `company` (company information)
  - `job_benefit` (job benefits)

**Expected Output:**

```
✅ Database tables created successfully!
📋 Created tables: [user, candidate_profile, recruiter_profile, ...]
```

---

### Step 5: (Optional) Load Sample Data

If you want to populate the database with sample job postings from CSV files:

```bash
python data/data_loader.py
```

**What this does:**

- Loads companies from `data/companies.csv`
- Loads job postings from `data/job_postings.csv`
- Loads job benefits from `data/benefits.csv`

**Note:** This step is OPTIONAL. You can skip it and create jobs manually through the recruiter interface.

If CSV files are missing, the script will show warnings but won't crash. You can start with an empty database.

---

### Step 6: Run the Application

```bash
python app.py
```

**Expected Output:**

```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

The application will be available at: **http://localhost:5000**

---

## ✅ Verify Installation

### Test 1: Access the Homepage

1. Open browser and go to `http://localhost:5000`
2. You should see the landing page
3. Navigation bar should show "Login" and "Sign Up"

### Test 2: Check Database

```bash
# Check if database file was created
ls database/job_portal.db  # Linux/Mac
dir database\job_portal.db  # Windows
```

### Test 3: Create Test Account

1. Click "Sign Up" on the website
2. Create a candidate account
3. Login with credentials
4. You should see the candidate dashboard

---

## 🎯 Quick Start Usage

### As a Candidate:

1. **Register** → Select "Candidate" as user type
2. **Login** with your credentials
3. **Upload Resume** → Go to dashboard → "Upload Resume"
4. Wait for AI analysis (10-15 seconds)
5. **View Job Recommendations** → AI will match you with jobs
6. **Browse Jobs** → Apply to jobs you like
7. **Track Applications** → View your applications

### As a Recruiter:

1. **Register** → Select "Recruiter" as user type
2. **Login** with your credentials
3. **Post a Job** → Fill in job details, skills, salary
4. **View Applications** → See candidates who applied
5. **Manage Jobs** → Activate/deactivate job postings

---

## 📁 Project Structure

```
job_portal/
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
│
├── database/
│   ├── __init__.py
│   ├── db_setup.py        # Database initialization script
│   ├── models.py          # Database models
│   └── job_portal.db      # SQLite database (created after setup)
│
├── ai_engine/
│   ├── __init__.py
│   ├── resume_parser.py   # AI resume parsing
│   ├── job_matcher.py     # AI job matching
│   ├── skill_analyzer.py  # Skill gap analysis
│   └── career_advisor.py  # Career advice generation
│
├── data/
│   ├── data_loader.py     # CSV data loader (optional)
│   ├── companies.csv      # Sample company data
│   ├── job_postings.csv   # Sample job data
│   └── benefits.csv       # Sample benefits data
│
├── templates/             # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── candidate/         # Candidate pages
│   └── recruiter/         # Recruiter pages
│
├── static/
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── uploads/          # Resume uploads (created automatically)
│
└── instance/             # Flask instance folder (auto-created)
```

---

## 🔧 Configuration Options

Edit `config.py` to customize:

### AI Model Settings:

```python
GROQ_MODEL = 'llama-3.1-8b-instant'  # Fast and free
# Alternatives: 'llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma2-9b-it'
```

### Job Matching Settings:

```python
TOP_JOBS_COUNT = 3              # Number of recommendations to show
MINIMUM_MATCH_SCORE = 0         # Minimum match percentage (0-100)
ALWAYS_SHOW_MIN_JOBS = 1        # Always show at least this many jobs
```

### Upload Settings:

```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'docx'}    # Allowed resume formats
```

---

## 🧪 Testing the Application

### End-to-End Candidate Flow:

1. **Register** as candidate: `http://localhost:5000/register`
2. **Login**: `http://localhost:5000/login`
3. **Upload Resume**: `http://localhost:5000/candidate/upload-resume`
4. **View Analysis**: `http://localhost:5000/candidate/resume-analysis`
5. **Job Recommendations**: `http://localhost:5000/candidate/job-recommendations`
6. **Browse All Jobs**: `http://localhost:5000/jobs`
7. **Apply to Jobs**: Click job → Apply Now
8. **View Applications**: `http://localhost:5000/candidate/applications`
9. **Career Map**: `http://localhost:5000/candidate/career-map`

### End-to-End Recruiter Flow:

1. **Register** as recruiter: `http://localhost:5000/register`
2. **Login**: `http://localhost:5000/login`
3. **Post Job**: `http://localhost:5000/recruiter/post-job`
4. **View Dashboard**: `http://localhost:5000/recruiter/dashboard`
5. **View Applications**: Click on job → View applications
6. **Update Profile**: `http://localhost:5000/recruiter/profile`

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution:** Make sure virtual environment is activated and dependencies are installed

```bash
pip install -r requirements.txt
```

### Issue: Database errors

**Solution:** Delete database and reinitialize

```bash
rm database/job_portal.db  # Linux/Mac
del database\job_portal.db  # Windows
python database/db_setup.py
```

### Issue: "Groq API error"

**Solution:**

- Check your API key in `.env` file
- Verify you have internet connection
- Ensure API key is valid at https://console.groq.com/

### Issue: Resume parsing fails

**Solution:**

- Check file format (must be PDF or DOCX)
- File size must be under 16MB
- Try a different resume file

### Issue: No job recommendations

**Solution:**

- Make sure at least one recruiter has posted a job
- Check that your resume was successfully uploaded and analyzed
- Try refreshing recommendations from the dashboard

### Issue: Port 5000 already in use

**Solution:** Run on a different port

```bash
# In app.py, change the last line to:
app.run(debug=True, port=5001)
```

### Issue: ML models downloading slowly

**Solution:** First-time setup downloads ~90MB of AI models. This is normal. Be patient and ensure stable internet connection.

---

## 🔒 Security Notes

**For Development:**

- Default SECRET_KEY is fine for testing
- SQLite database is used (simple, file-based)
- Debug mode is ON for helpful error messages

**For Production Deployment:**

- Change SECRET_KEY to a strong random string
- Use PostgreSQL or MySQL instead of SQLite
- Set `debug=False` in app.py
- Use environment variables for all secrets
- Use HTTPS
- Set up proper authentication
- Add rate limiting
- Use gunicorn or similar WSGI server

---

## 📊 Database Schema

### Key Tables:

**Users:**

- Stores authentication for both candidates and recruiters
- Fields: email, password_hash, user_type

**Candidate Profile:**

- Stores candidate information and resume analysis
- Fields: skills, experience, resume_path, resume_score

**Recruiter Profile:**

- Stores recruiter and company information
- Fields: company_name, company_description, location

**Job Posting:**

- Stores job listings
- Fields: title, description, skills, salary, source (recruiter/dataset)

**Application:**

- Tracks job applications
- Fields: candidate_id, job_id, status, match_score

**Job Recommendation:**

- AI-generated job matches
- Fields: candidate_id, job_id, match_score, reasons

---

## 🚀 Advanced Features

### AI-Powered Features:

1. **Resume Parsing:**
   - Extracts name, skills, experience, education
   - Detects career domain automatically
   - Calculates resume quality score

2. **Job Matching:**
   - Semantic similarity using Sentence-BERT
   - Skills overlap analysis
   - Experience level matching
   - Location preferences
   - Salary expectations

3. **Career Advisor:**
   - Personalized career advice
   - Role transition roadmaps
   - Industry insights
   - Interview preparation guides

4. **Skill Gap Analysis:**
   - Identifies missing skills for target roles
   - Generates learning paths
   - Recommends free resources
   - Career progression mapping

---

## 📞 Support

If you encounter issues:

1. Check this SETUP.md file
2. Review error messages in terminal
3. Check browser console (F12) for JavaScript errors
4. Verify all prerequisites are met
5. Try recreating the database from scratch

---

## 🎉 You're All Set!

Your AI Job Portal is now ready to use. Start by:

1. Creating a recruiter account and posting some jobs
2. Creating a candidate account and uploading a resume
3. Exploring the AI-powered matching and recommendations

**Happy Job Hunting! 🚀**
