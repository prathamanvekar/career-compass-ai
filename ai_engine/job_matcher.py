import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import Config


class JobMatcher:
    """Match candidates with jobs using Sentence-BERT embeddings"""

    _model = None  # Class-level model cache

    def __init__(self):
        # Load Sentence-BERT model (downloads on first use ~90MB)
        # Using class-level caching to avoid reloading
        if JobMatcher._model is None:
            print("Loading Sentence-BERT model... (this may take a moment on first run)")
            JobMatcher._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Sentence-BERT model loaded successfully!")

        self.model = JobMatcher._model

        # Weights for different matching criteria
        self.weights = {
            'semantic_similarity': 0.40,  # Overall semantic match
            'skills_match': 0.30,         # Skills overlap
            'experience_match': 0.15,     # Experience level match
            'location_match': 0.10,       # Location preference
            'salary_match': 0.05          # Salary expectation
        }

    def create_candidate_text(self, profile):
        """Create searchable text from candidate profile"""
        parts = []

        if profile.get('detected_domain'):
            parts.append(f"Domain: {profile['detected_domain']}")

        if profile.get('skills'):
            skills = profile['skills'] if isinstance(profile['skills'], list) else []
            if isinstance(profile['skills'], str):
                try:
                    skills = json.loads(profile['skills'])
                except:
                    skills = []
            if skills:
                parts.append(f"Skills: {', '.join(skills)}")

        if profile.get('experience_level'):
            parts.append(f"Experience Level: {profile['experience_level']}")

        if profile.get('work_history'):
            work = profile['work_history'] if isinstance(profile['work_history'], list) else []
            if isinstance(profile['work_history'], str):
                try:
                    work = json.loads(profile['work_history'])
                except:
                    work = []
            for job in work[:3]:  # Latest 3 jobs
                if isinstance(job, dict):
                    parts.append(f"Previous Role: {job.get('title', '')} at {job.get('company', '')}")

        if profile.get('summary'):
            parts.append(f"Summary: {profile['summary']}")

        return " | ".join(parts) if parts else "General candidate profile"

    def create_job_text(self, job):
        """Create searchable text from job posting"""
        parts = []

        if job.get('title'):
            parts.append(f"Title: {job['title']}")

        if job.get('description'):
            # Limit description length
            desc = str(job['description'])[:1000]
            parts.append(f"Description: {desc}")

        if job.get('required_skills'):
            skills = job['required_skills']
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = []
            if skills and isinstance(skills, list):
                parts.append(f"Required Skills: {', '.join(skills)}")

        if job.get('skills_description'):
            parts.append(f"Skills: {job['skills_description']}")

        if job.get('experience_level'):
            parts.append(f"Experience: {job['experience_level']}")

        return " | ".join(parts) if parts else "General job posting"

    def get_embedding(self, text):
        """Generate embedding for text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding

    def calculate_semantic_similarity(self, candidate_embedding, job_embedding):
        """Calculate cosine similarity between embeddings"""
        similarity = cosine_similarity(
            candidate_embedding.reshape(1, -1),
            job_embedding.reshape(1, -1)
        )[0][0]
        return float(similarity)

    def calculate_skills_match(self, candidate_skills, job_skills):
        """Calculate skills overlap percentage"""
        if not candidate_skills or not job_skills:
            return 0.5  # Neutral if missing data

        # Normalize skills to lowercase
        candidate_set = set(s.lower().strip() for s in candidate_skills if s)
        job_set = set(s.lower().strip() for s in job_skills if s)

        if not job_set:
            return 0.5

        # Calculate intersection
        matched = candidate_set.intersection(job_set)
        match_ratio = len(matched) / len(job_set)

        return match_ratio

    def calculate_experience_match(self, candidate_level, job_level):
        """Calculate experience level match"""
        level_order = ['entry', 'associate', 'mid', 'mid-senior', 'senior', 'director', 'executive']

        # Normalize levels
        candidate_level_norm = str(candidate_level).lower().strip() if candidate_level else 'mid'
        job_level_norm = str(job_level).lower().strip() if job_level else 'mid'

        # Handle variations
        level_mapping = {
            'entry level': 'entry',
            'entry-level': 'entry',
            'junior': 'entry',
            'mid-senior level': 'mid-senior',
            'mid senior level': 'mid-senior',
            'senior level': 'senior',
            'senior-level': 'senior',
            'lead': 'senior',
            'principal': 'director',
            'manager': 'director',
            'vp': 'executive',
            'c-level': 'executive'
        }

        candidate_level_norm = level_mapping.get(candidate_level_norm, candidate_level_norm)
        job_level_norm = level_mapping.get(job_level_norm, job_level_norm)

        try:
            candidate_idx = level_order.index(candidate_level_norm)
        except ValueError:
            candidate_idx = 2  # Default to mid

        try:
            job_idx = level_order.index(job_level_norm)
        except ValueError:
            job_idx = 2  # Default to mid

        # Calculate match (penalize being under-qualified more than over-qualified)
        diff = candidate_idx - job_idx

        if diff == 0:
            return 1.0
        elif diff > 0:  # Over-qualified
            return max(0.5, 1.0 - (diff * 0.15))
        else:  # Under-qualified
            return max(0.2, 1.0 + (diff * 0.25))

    def calculate_location_match(self, candidate_location, job_location, remote_allowed):
        """Calculate location preference match"""
        if remote_allowed:
            return 1.0

        if not candidate_location or not job_location:
            return 0.7  # Neutral

        # Simple string matching
        candidate_loc = str(candidate_location).lower()
        job_loc = str(job_location).lower()

        if candidate_loc in job_loc or job_loc in candidate_loc:
            return 1.0

        # Check for state/city match
        candidate_parts = set(candidate_loc.replace(',', ' ').split())
        job_parts = set(job_loc.replace(',', ' ').split())

        if candidate_parts.intersection(job_parts):
            return 0.8

        return 0.5

    def calculate_salary_match(self, candidate_min, candidate_max, job_min, job_max):
        """Calculate salary expectation match"""
        if not job_max or not candidate_min:
            return 0.7  # Neutral if missing data

        try:
            candidate_min = float(candidate_min)
            job_max = float(job_max)
        except (ValueError, TypeError):
            return 0.7

        if candidate_min <= job_max:
            if candidate_max and job_min:
                try:
                    if float(candidate_max) >= float(job_min):
                        return 1.0
                except (ValueError, TypeError):
                    pass
            return 0.8

        return 0.3

    def get_match_reasons(self, candidate_profile, job, scores):
        """Generate human-readable match reasons"""
        reasons = []

        # Skills match
        if scores.get('skills_match', 0) > 0.3:
            candidate_skills = candidate_profile.get('skills', [])
            job_skills = job.get('required_skills', [])

            if isinstance(candidate_skills, str):
                try:
                    candidate_skills = json.loads(candidate_skills)
                except:
                    candidate_skills = []

            if isinstance(job_skills, str):
                try:
                    job_skills = json.loads(job_skills)
                except:
                    job_skills = []

            if candidate_skills and job_skills:
                matched = set(s.lower() for s in candidate_skills if s) & set(s.lower() for s in job_skills if s)
                if matched:
                    reasons.append(f"Skill match: {', '.join(list(matched)[:5])}")

        # Semantic match
        if scores.get('semantic_similarity', 0) > 0.5:
            reasons.append("Your profile aligns with job requirements")

        # Experience match
        if scores.get('experience_match', 0) > 0.7:
            exp_level = job.get('experience_level', 'N/A')
            if exp_level and exp_level != 'N/A':
                reasons.append(f"Experience level: {exp_level}")

        # Location
        if scores.get('location_match', 0) >= 0.8:
            if job.get('remote_allowed'):
                reasons.append("Remote work available")
            else:
                location = job.get('location')
                if location:
                    reasons.append(f"Location: {location}")

        # Domain match
        if candidate_profile.get('detected_domain'):
            domain = str(candidate_profile['detected_domain']).lower()
            title = str(job.get('title', '')).lower()
            if any(word in title for word in domain.split() if len(word) > 3):
                reasons.append(f"Matches your domain: {candidate_profile['detected_domain']}")

        # Default reason if none found
        if not reasons:
            if job.get('title'):
                reasons.append(f"Potential opportunity: {job.get('title')}")
            else:
                reasons.append("Available position matching your profile")

        return reasons

    def match_candidate_to_job(self, candidate_profile, job, candidate_embedding=None, job_embedding=None):
        """Calculate overall match score between candidate and job"""

        # Generate embeddings if not provided
        if candidate_embedding is None:
            candidate_text = self.create_candidate_text(candidate_profile)
            candidate_embedding = self.get_embedding(candidate_text)

        if job_embedding is None:
            job_text = self.create_job_text(job)
            job_embedding = self.get_embedding(job_text)

        # Calculate individual scores
        scores = {}

        # Semantic similarity
        scores['semantic_similarity'] = self.calculate_semantic_similarity(
            candidate_embedding, job_embedding
        )

        # Skills match
        candidate_skills = candidate_profile.get('skills', [])
        if isinstance(candidate_skills, str):
            try:
                candidate_skills = json.loads(candidate_skills)
            except:
                candidate_skills = []

        job_skills = job.get('required_skills', [])
        if isinstance(job_skills, str):
            try:
                job_skills = json.loads(job_skills)
            except:
                job_skills = []

        # If no parsed skills, try skills_description
        if not job_skills and job.get('skills_description'):
            job_skills = [s.strip() for s in str(job['skills_description']).split(',')]

        scores['skills_match'] = self.calculate_skills_match(candidate_skills, job_skills)

        # Experience match
        scores['experience_match'] = self.calculate_experience_match(
            candidate_profile.get('experience_level', 'mid'),
            job.get('experience_level', 'mid')
        )

        # Location match
        scores['location_match'] = self.calculate_location_match(
            candidate_profile.get('preferred_location') or candidate_profile.get('location'),
            job.get('location'),
            job.get('remote_allowed', False)
        )

        # Salary match
        scores['salary_match'] = self.calculate_salary_match(
            candidate_profile.get('preferred_salary_min'),
            candidate_profile.get('preferred_salary_max'),
            job.get('min_salary'),
            job.get('max_salary')
        )

        # Calculate weighted overall score
        overall_score = sum(
            scores[key] * self.weights[key]
            for key in self.weights
        )

        # Convert to percentage
        match_percentage = round(overall_score * 100, 1)

        # Get match reasons
        reasons = self.get_match_reasons(candidate_profile, job, scores)

        return {
            'match_score': match_percentage,
            'detailed_scores': scores,
            'reasons': reasons,
            'candidate_embedding': candidate_embedding,
            'job_embedding': job_embedding
        }

    def find_top_matches(self, candidate_profile, jobs, top_n=3):
        """Find top N matching jobs for a candidate"""

        if not jobs:
            return []

        # Generate candidate embedding once
        candidate_text = self.create_candidate_text(candidate_profile)
        candidate_embedding = self.get_embedding(candidate_text)

        matches = []

        for job in jobs:
            try:
                result = self.match_candidate_to_job(
                    candidate_profile,
                    job,
                    candidate_embedding=candidate_embedding
                )

                matches.append({
                    'job': job,
                    'match_score': result['match_score'],
                    'reasons': result['reasons'],
                    'detailed_scores': result['detailed_scores']
                })
            except Exception as e:
                print(f"Error matching job {job.get('id', 'unknown')}: {e}")
                continue

        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        # Get minimum score from config, default to 0
        min_score = getattr(Config, 'MINIMUM_MATCH_SCORE', 0)

        # Filter by minimum score
        filtered_matches = [m for m in matches if m['match_score'] >= min_score]

        # Ensure at least ALWAYS_SHOW_MIN_JOBS jobs are returned
        min_jobs = getattr(Config, 'ALWAYS_SHOW_MIN_JOBS', 1)

        if len(filtered_matches) < min_jobs and len(matches) > 0:
            # Include more jobs even if below threshold
            filtered_matches = matches[:max(min_jobs, len(filtered_matches))]

        return filtered_matches[:top_n]


# Quick function for matching
def get_job_recommendations(candidate_profile, jobs, top_n=3):
    """Get top job recommendations for a candidate"""
    matcher = JobMatcher()
    return matcher.find_top_matches(candidate_profile, jobs, top_n)
