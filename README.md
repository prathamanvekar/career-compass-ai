# Career Compass AI

An AI-powered job portal connecting candidates and recruiters with intelligent resume parsing, semantic job matching, skill gap analysis, and career guidance powered by LLM.

---

## 🌟 Features

### For Candidates

- **Smart Resume Analysis**: Upload and parse resumes with AI-powered extraction of skills, experience, and education
- **Resume Score & Suggestions**: Get actionable feedback on resume quality and improvement recommendations
- **Intelligent Job Recommendations**: Receive job suggestions based on semantic matching of skills and experience
- **Career Guidance**: Get professional career advice and development path recommendations powered by AI
- **Skill Gap Analysis**: Identify missing skills for target roles and get learning recommendations
- **Application Tracking**: View and manage all job applications in one place

### For Recruiters

- **Post Job Openings**: Create and manage job listings with detailed requirements
- **View Applications**: Review applications from candidates matching your postings
- **Manage Postings**: Update or deactivate job listings anytime
- **Company Profile**: Build your company profile to attract top talent

### AI-Powered Capabilities

- **Sentence-BERT Embeddings**: Semantic understanding of job descriptions and candidate profiles for accurate matching
- **Resume Parsing**: Automatic extraction of skills, experience level, domain, and education from resume files (PDF, DOCX)
- **Groq LLM Integration**: Free, fast AI for career advice and skill gap analysis using Llama 3.1
- **Multi-criterion Matching**: Candidates matched based on semantic similarity, skills, experience level, location, and salary expectations

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or higher**
- **pip** (Python package manager)
- **Virtual environment** tool (recommended)
- **Free Groq API key** from [https://console.groq.com/](https://console.groq.com/)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd career-compass-ai
```

### 2. Create and Activate Virtual Environment

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/macOS:**

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here-change-in-production
GROQ_API_KEY=your-groq-api-key-from-console.groq.com
```

**To generate a secret key:**

```python
import secrets
print(secrets.token_hex(32))
```

### 5. Initialize the Database

```bash
python
>>> from database import db
>>> from app import app
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 6. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

---

## 📁 Project Structure

```
career-compass-ai/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
│
├── ai_engine/                  # AI/ML functionality
│   ├── career_advisor.py       # Career guidance using Groq LLM
│   ├── job_matcher.py          # Semantic job matching with embeddings
│   ├── resume_parser.py        # Resume parsing and text extraction
│   └── skill_analyzer.py       # Skill extraction and gap analysis
│
├── database/                   # Database layer
│   ├── models.py               # SQLAlchemy models
│   ├── db_setup.py             # Database initialization
│   └── job_portal.db           # SQLite database (created automatically)
│
├── data/                       # Data files and loading
│   ├── jobs.csv               # Job listings dataset
│   ├── companies.csv          # Company information
│   ├── benefits.csv           # Job benefits data
│   └── data_loader.py         # CSV data loading utilities
│
├── static/                     # Static files
│   ├── css/style.css          # Styling
│   ├── js/main.js             # Frontend JavaScript
│   └── uploads/               # Resume upload folder
│
└── templates/                  # HTML templates
    ├── base.html              # Base template
    ├── index.html             # Landing page
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── jobs.html              # Job listings
    ├── job_detail.html        # Individual job details
    ├── candidate/             # Candidate-specific templates
    │   ├── dashboard.html
    │   ├── job_recommendations.html
    │   ├── upload_resume.html
    │   ├── resume_analysis.html
    │   ├── career_map.html
    │   └── applications.html
    ├── recruiter/             # Recruiter-specific templates
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── post_job.html
    │   └── view_applications.html
    └── errors/                # Error pages
        ├── 404.html
        └── 500.html
```

---

## 🔑 Key Technologies

- **Backend**: Flask, SQLAlchemy (ORM), SQLite
- **AI/ML**: Sentence-BERT, Groq LLM API, scikit-learn
- **Resume Processing**: PyPDF2, python-docx, pdfplumber
- **Frontend**: Jinja2 templates, HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login with password hashing

---

## 🎯 Usage

### For Candidates

1. **Register** with your email and create a password
2. **Upload Resume**: Upload your resume (PDF or DOCX format) on dashboard
3. **View Analysis**: Get resume scoring and improvement suggestions
4. **Get Recommendations**: Browse AI-matched job recommendations
5. **Apply to Jobs**: Submit applications directly from job listings
6. **Career Advice**: Ask for career guidance based on your profile
7. **Track Skills**: Identify skill gaps for target roles

### For Recruiters

1. **Register** as a recruiter with company details
2. **Post Jobs**: Create new job postings with title, description, and requirements
3. **Manage Listings**: View active postings and update/deactivate as needed
4. **Review Applications**: Check applications received for each posting
5. **Find Candidates**: Browse candidates or enable matching system to find suitable candidates

---

## 🤖 AI Features Explained

### Resume Parsing

- Extracts skills, experience, education, and domain information
- Uses OCR and text extraction for accurate data capture
- Provides resume quality score with enhancement suggestions

### Job Matching

- Uses Sentence-BERT for semantic understanding
- Matches candidates based on:
  - Semantic similarity (40%)
  - Skills match (30%)
  - Experience level (15%)
  - Location preference (10%)
  - Salary expectations (5%)

### Career Advisor

- Powered by Groq's Llama 3.1 model
- Provides personalized career path recommendations
- Offers professional development guidance based on current skills

### Skill Gap Analysis

- Identifies missing skills for target positions
- Recommends learning resources
- Tracks skill development progress

---

## 📦 Dependencies

- **flask** - Web framework
- **flask-sqlalchemy** - ORM
- **flask-login** - Authentication
- **sentence-transformers** - Semantic embeddings (~90MB model)
- **groq** - Free LLM API for career advice
- **language-tool-python** - Text validation
- **PyPDF2, python-docx, pdfplumber** - Document processing
- **pandas, numpy, scikit-learn** - Data processing and ML
- **python-dotenv** - Environment management

---

## ⚙️ Configuration

Edit `config.py` or `.env` to customize:

- `SECRET_KEY`: Flask secret key (change for production)
- `GROQ_API_KEY`: Your Groq API key for career advice
- `GROQ_MODEL`: Change to `llama-3.1-70b-versatile` for more powerful responses (slower)
- `MAX_CONTENT_LENGTH`: Max resume file size (default: 16MB)
- `ALLOWED_EXTENSIONS`: Supported resume formats (default: `pdf`, `docx`)
- `SQLALCHEMY_DATABASE_URI`: Database location

---

## 🧪 Testing

To test the application:

1. Register as both a candidate and recruiter
2. Upload a sample resume as candidate
3. Post a job as recruiter
4. Check if job recommendations appear
5. Test career advisor with various questions
6. Apply to jobs and verify applications appear

---

## 🔒 Security Notes

- Change `SECRET_KEY` in production
- Store `GROQ_API_KEY` in `.env` file (never commit to git)
- Add `.env` to `.gitignore`
- Use HTTPS in production
- Validate all file uploads
- Implement rate limiting for API calls

---

## 📝 Database Models

### User

- Handles both candidate and recruiter authentication
- Relationships to candidate and recruiter profiles

### CandidateProfile

- Stores resume data, extracted skills, experience level
- Tracks resume embedding for matching

### RecruiterProfile

- Stores company information and contact details

### JobPosting

- Supports both dataset and recruiter-created jobs
- Contains job details and matching embeddings

### Application

- Tracks applications from candidates to job postings

### JobRecommendation

- Stores AI-generated recommendations for candidates

### SkillGapAnalysis

- Analysis of missing skills for target positions

---

## 🤝 Contributing

Feel free to contribute by:

1. Reporting bugs or issues
2. Suggesting new features
3. Improving documentation
4. Optimizing AI matching algorithms

---

## 📄 License

This project is open source. Check LICENSE file for details.

---

## 📧 Support

For issues or questions, please reach out to the development team.

---

## 🚀 Future Enhancements

- [ ] Resume skill extraction using NLP
- [ ] Video interview integration
- [ ] Salary prediction based on skills
- [ ] More sophisticated skill gap analysis
- [ ] Integration with LinkedIn and Indeed APIs
- [ ] Mobile app version
- [ ] Advanced analytics dashboard for recruiters
- [ ] Email notifications system
- [ ] Offline resume analysis capability

---

**Pro Tip**: First run will download a ~90MB Sentence-BERT model. Subsequent runs will be faster!
