import json
from groq import Groq
from config import Config

# Initialize Groq client
client = Groq(api_key=Config.GROQ_API_KEY)


class SkillAnalyzer:
    """Analyze skill gaps and provide learning recommendations using Groq"""

    def __init__(self):
        self.model = Config.GROQ_MODEL

    def _call_groq(self, prompt):
        """Make a call to Groq API"""
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career advisor and skill analyst. Always respond with valid JSON only, no additional text or markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=4096,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API error: {e}")
            raise e

    def _clean_json_response(self, response_text):
        """Clean and parse JSON from response"""
        response_text = response_text.strip()

        # Remove markdown code blocks
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            start_idx = 1 if lines[0].startswith('```') else 0
            end_idx = len(lines) - 1 if lines[-1].strip() == '```' else len(lines)
            response_text = '\n'.join(lines[start_idx:end_idx])

        response_text = response_text.replace('```json', '').replace('```', '').strip()

        return json.loads(response_text)

    def analyze_skill_gap(self, candidate_skills, target_job_skills, target_role=None):
        """Analyze gap between candidate skills and target job requirements"""

        # Convert to lists if needed
        if isinstance(candidate_skills, str):
            candidate_skills = json.loads(candidate_skills) if candidate_skills else []
        if isinstance(target_job_skills, str):
            target_job_skills = json.loads(target_job_skills) if target_job_skills else []

        # Normalize skills
        candidate_set = set(s.lower().strip() for s in candidate_skills)
        target_set = set(s.lower().strip() for s in target_job_skills)

        # Rule-based analysis
        matched_skills = candidate_set.intersection(target_set)
        missing_skills = target_set - candidate_set
        extra_skills = candidate_set - target_set

        # Calculate match percentage
        if target_set:
            match_percentage = (len(matched_skills) / len(target_set)) * 100
        else:
            match_percentage = 100

        return {
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'extra_skills': list(extra_skills),
            'match_percentage': round(match_percentage, 1),
            'skills_to_acquire': len(missing_skills)
        }

    def get_learning_path(self, missing_skills, target_role=None, current_domain=None):
        """Generate learning path for missing skills using Groq"""

        if not missing_skills:
            return {
                'message': 'No skill gaps identified!',
                'recommendations': []
            }

        # Limit skills to avoid token limits
        missing_skills = missing_skills[:10]

        prompt = f"""Create a learning path for someone who needs to learn these skills:

Missing Skills: {', '.join(missing_skills)}
Target Role: {target_role or 'General career advancement'}
Current Domain: {current_domain or 'Not specified'}

Provide a structured learning plan in JSON format:
{{
    "learning_path": [
        {{
            "skill": "skill name",
            "priority": "high/medium/low",
            "estimated_time": "e.g., 2-4 weeks",
            "resources": [
                {{
                    "type": "course/tutorial/book/project",
                    "name": "resource name",
                    "platform": "platform name (use free platforms like Coursera free courses, YouTube, freeCodeCamp, Khan Academy, etc.)",
                    "url": "leave empty",
                    "is_free": true
                }}
            ],
            "practice_projects": ["project idea 1", "project idea 2"]
        }}
    ],
    "recommended_order": ["skill1", "skill2", "skill3"],
    "total_estimated_time": "e.g., 3-6 months",
    "milestones": [
        {{
            "milestone": "milestone description",
            "skills_completed": ["skills"],
            "expected_timeline": "e.g., Month 1"
        }}
    ]
}}

Focus on FREE resources. Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            learning_plan = self._clean_json_response(response_text)
            return learning_plan

        except Exception as e:
            print(f"Error generating learning path: {e}")
            # Return basic recommendations
            return {
                'learning_path': [
                    {
                        'skill': skill,
                        'priority': 'medium',
                        'estimated_time': '2-4 weeks',
                        'resources': [
                            {
                                'type': 'course',
                                'name': f'Learn {skill}',
                                'platform': 'YouTube/Coursera',
                                'is_free': True
                            }
                        ],
                        'practice_projects': [f'Build a project using {skill}']
                    }
                    for skill in missing_skills[:5]
                ],
                'recommended_order': missing_skills[:5],
                'total_estimated_time': '2-3 months'
            }

    def get_career_progression(self, current_profile, target_role=None):
        """Generate career progression roadmap"""

        current_skills = current_profile.get('skills', [])
        current_domain = current_profile.get('detected_domain', 'General')
        experience_level = current_profile.get('experience_level', 'mid')
        experience_years = current_profile.get('experience_years', 0)

        if isinstance(current_skills, str):
            current_skills = json.loads(current_skills) if current_skills else []

        # Limit skills for prompt
        skills_str = ', '.join(current_skills[:15])

        prompt = f"""Create a career progression roadmap for this professional:

Current Profile:
- Domain: {current_domain}
- Experience: {experience_years} years ({experience_level} level)
- Current Skills: {skills_str}
- Target Role: {target_role or 'Next logical career step'}

Generate a career roadmap in JSON format:
{{
    "current_position": {{
        "title": "estimated current title",
        "level": "junior/mid/senior",
        "market_value": "estimated salary range"
    }},
    "short_term_goals": {{
        "timeline": "6-12 months",
        "target_role": "next role",
        "skills_needed": ["skill1", "skill2"],
        "actions": ["action1", "action2"]
    }},
    "mid_term_goals": {{
        "timeline": "1-3 years",
        "target_role": "role title",
        "skills_needed": ["skills"],
        "actions": ["actions"]
    }},
    "long_term_goals": {{
        "timeline": "3-5 years",
        "target_roles": ["potential role 1", "potential role 2"],
        "leadership_skills": ["skills for leadership"],
        "specialization_options": ["option1", "option2"]
    }},
    "career_paths": [
        {{
            "path_name": "e.g., Technical Track",
            "progression": ["Current", "Role 2", "Role 3", "Role 4"],
            "key_skills": ["skills needed"],
            "typical_timeline": "X years"
        }},
        {{
            "path_name": "e.g., Management Track",
            "progression": ["roles"],
            "key_skills": ["skills"],
            "typical_timeline": "X years"
        }}
    ],
    "industry_insights": {{
        "growing_areas": ["area1", "area2"],
        "skills_in_demand": ["skill1", "skill2"],
        "salary_growth_potential": "percentage or description"
    }}
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            career_map = self._clean_json_response(response_text)
            return career_map

        except Exception as e:
            print(f"Error generating career progression: {e}")
            return {
                'current_position': {
                    'title': f'{experience_level.title()} {current_domain} Professional',
                    'level': experience_level
                },
                'short_term_goals': {
                    'timeline': '6-12 months',
                    'target_role': 'Senior position',
                    'skills_needed': ['Leadership', 'Advanced technical skills'],
                    'actions': ['Take on more responsibility', 'Complete relevant certifications']
                },
                'career_paths': [
                    {
                        'path_name': 'Technical Track',
                        'progression': ['Current Role', 'Senior Role', 'Lead/Architect'],
                        'typical_timeline': '5-7 years'
                    }
                ]
            }


def analyze_candidate_skills(candidate_profile, target_jobs=None):
    """Analyze candidate skills and provide recommendations"""
    analyzer = SkillAnalyzer()

    # Aggregate skills from target jobs
    target_skills = set()
    if target_jobs:
        for job in target_jobs:
            skills = job.get('required_skills', [])
            if isinstance(skills, str):
                skills = json.loads(skills) if skills else []
            target_skills.update(s.lower().strip() for s in skills)

    # Perform gap analysis
    gap_analysis = analyzer.analyze_skill_gap(
        candidate_profile.get('skills', []),
        list(target_skills)
    )

    # Get learning path if there are missing skills
    learning_path = None
    if gap_analysis['missing_skills']:
        learning_path = analyzer.get_learning_path(
            gap_analysis['missing_skills'],
            target_role=None,
            current_domain=candidate_profile.get('detected_domain')
        )

    # Get career progression
    career_map = analyzer.get_career_progression(candidate_profile)

    return {
        'gap_analysis': gap_analysis,
        'learning_path': learning_path,
        'career_map': career_map
    }
