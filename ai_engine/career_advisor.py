import json
from groq import Groq
from config import Config

# Initialize Groq client
client = Groq(api_key=Config.GROQ_API_KEY)


class CareerAdvisor:
    """Generate career advice, path suggestions, and professional guidance using Groq AI"""

    def __init__(self):
        self.model = Config.GROQ_MODEL

    def _call_groq(self, prompt):
        """Make a call to Groq API"""
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career advisor with expertise in various industries. Always respond with valid JSON only, no additional text or markdown."
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

    def get_career_advice(self, candidate_profile, target_role=None):
        """Generate personalized career advice based on candidate profile"""

        # Extract profile data
        current_skills = candidate_profile.get('skills', [])
        if isinstance(current_skills, str):
            current_skills = json.loads(current_skills) if current_skills else []

        domain = candidate_profile.get('detected_domain', 'General')
        experience_level = candidate_profile.get('experience_level', 'mid')
        experience_years = candidate_profile.get('experience_years', 0)

        work_history = candidate_profile.get('work_history', [])
        if isinstance(work_history, str):
            work_history = json.loads(work_history) if work_history else []

        education = candidate_profile.get('education', [])
        if isinstance(education, str):
            education = json.loads(education) if education else []

        # Prepare summary strings
        skills_str = ', '.join(current_skills[:20])
        roles_str = ', '.join([w.get('title', '') for w in work_history[:3]])
        edu_str = ', '.join([e.get('degree', '') + ' in ' + e.get('field', '') for e in education[:2]])

        prompt = f"""Act as a professional career advisor. Analyze this candidate's profile and provide comprehensive career advice.

CANDIDATE PROFILE:
- Current Domain: {domain}
- Experience Level: {experience_level}
- Years of Experience: {experience_years}
- Skills: {skills_str}
- Recent Roles: {roles_str}
- Education: {edu_str}
- Target Role (if specified): {target_role or 'Not specified - suggest best options'}

Provide detailed career advice in JSON format:
{{
    "career_summary": {{
        "current_standing": "Assessment of where they stand in their career",
        "strengths": ["key strength 1", "key strength 2", "key strength 3"],
        "areas_for_growth": ["area 1", "area 2"],
        "market_position": "How competitive they are in current job market"
    }},
    "recommended_roles": [
        {{
            "role_title": "Recommended job title",
            "match_reason": "Why this role suits them",
            "salary_range": "Expected salary range (USD)",
            "demand_level": "high/medium/low",
            "transition_difficulty": "easy/moderate/challenging"
        }}
    ],
    "immediate_actions": [
        {{
            "action": "Specific action to take",
            "timeline": "When to complete",
            "impact": "high/medium/low",
            "details": "How to accomplish this"
        }}
    ],
    "skill_development_priority": [
        {{
            "skill": "Skill name",
            "current_level": "beginner/intermediate/advanced/none",
            "target_level": "intermediate/advanced/expert",
            "importance": "Why this skill matters",
            "resources": ["Free resource 1", "Free resource 2"]
        }}
    ],
    "networking_advice": {{
        "platforms": ["Platform 1", "Platform 2"],
        "communities": ["Community/Group to join"],
        "events": ["Type of events to attend"],
        "tips": ["Networking tip 1", "Networking tip 2"]
    }},
    "long_term_vision": {{
        "5_year_outlook": "Where they could be in 5 years",
        "industry_trends": ["Trend 1", "Trend 2"],
        "future_proof_skills": ["Skill that will remain valuable"]
    }}
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            advice = self._clean_json_response(response_text)
            return advice

        except Exception as e:
            print(f"Error generating career advice: {e}")
            return self._get_default_advice(domain, experience_level)

    def get_role_roadmap(self, current_role, target_role, current_skills):
        """Generate a detailed roadmap to transition from current role to target role"""

        if isinstance(current_skills, str):
            current_skills = json.loads(current_skills) if current_skills else []

        skills_str = ', '.join(current_skills[:15])

        prompt = f"""Create a detailed career transition roadmap.

FROM: {current_role or 'Current Position'}
TO: {target_role}
CURRENT SKILLS: {skills_str}

Generate a step-by-step roadmap in JSON format:
{{
    "transition_overview": {{
        "feasibility": "highly feasible/feasible/challenging/very challenging",
        "estimated_timeline": "X-Y months",
        "difficulty_level": "1-10 scale",
        "success_factors": ["Factor 1", "Factor 2"]
    }},
    "phase_1_foundation": {{
        "duration": "X weeks/months",
        "focus": "What to focus on",
        "skills_to_acquire": ["Skill 1", "Skill 2"],
        "actions": [
            {{
                "task": "Specific task",
                "resources": ["Free resource"],
                "deliverable": "What to complete"
            }}
        ],
        "milestones": ["Milestone 1", "Milestone 2"]
    }},
    "phase_2_building": {{
        "duration": "X weeks/months",
        "focus": "What to focus on",
        "skills_to_acquire": ["Skill 1", "Skill 2"],
        "projects": ["Project to build 1", "Project to build 2"],
        "milestones": ["Milestone 1"]
    }},
    "phase_3_transition": {{
        "duration": "X weeks/months",
        "focus": "Job search and transition",
        "job_search_strategy": {{
            "target_companies": ["Type of companies to target"],
            "application_tips": ["Tip 1", "Tip 2"],
            "interview_prep": ["How to prepare"]
        }}
    }},
    "potential_challenges": [
        {{
            "challenge": "Potential obstacle",
            "solution": "How to overcome it"
        }}
    ]
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            roadmap = self._clean_json_response(response_text)
            return roadmap

        except Exception as e:
            print(f"Error generating role roadmap: {e}")
            return {
                "transition_overview": {
                    "feasibility": "feasible",
                    "estimated_timeline": "6-12 months",
                    "difficulty_level": 5
                },
                "phase_1_foundation": {
                    "duration": "1-2 months",
                    "focus": "Build foundational skills",
                    "actions": [{"task": "Research target role requirements"}]
                },
                "phase_2_building": {
                    "duration": "2-4 months",
                    "focus": "Develop key skills and build portfolio",
                    "projects": ["Create relevant projects"]
                },
                "phase_3_transition": {
                    "duration": "1-3 months",
                    "focus": "Job search and applications"
                }
            }

    def get_industry_insights(self, domain):
        """Get current industry insights and trends for a specific domain"""

        prompt = f"""Provide current industry insights for the {domain} field.

Generate insights in JSON format:
{{
    "industry_overview": {{
        "current_state": "Brief overview of the industry",
        "growth_outlook": "Growing/Stable/Declining",
        "market_size_trend": "Description of market trends"
    }},
    "in_demand_roles": [
        {{
            "role": "Job title",
            "demand_level": "high/medium",
            "average_salary": "Salary range USD",
            "growth_rate": "Percentage or description"
        }}
    ],
    "emerging_skills": [
        {{
            "skill": "Skill name",
            "why_important": "Reason",
            "adoption_timeline": "Now/1-2 years/3-5 years"
        }}
    ],
    "technology_trends": [
        {{
            "trend": "Technology or methodology",
            "impact": "How it affects the industry",
            "action": "What professionals should do"
        }}
    ],
    "salary_trends": {{
        "entry_level": "Range",
        "mid_level": "Range",
        "senior_level": "Range",
        "trend": "Increasing/Stable/Decreasing"
    }},
    "advice_for_professionals": [
        "Actionable advice 1",
        "Actionable advice 2",
        "Actionable advice 3"
    ]
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            insights = self._clean_json_response(response_text)
            return insights

        except Exception as e:
            print(f"Error getting industry insights: {e}")
            return {
                "industry_overview": {
                    "current_state": f"The {domain} industry is evolving",
                    "growth_outlook": "Growing"
                },
                "in_demand_roles": [],
                "emerging_skills": [],
                "advice_for_professionals": [
                    "Stay updated with latest trends",
                    "Build a strong professional network",
                    "Continue learning new skills"
                ]
            }

    def get_interview_preparation(self, role, skills, experience_level):
        """Generate interview preparation guide for a specific role"""

        if isinstance(skills, str):
            skills = json.loads(skills) if skills else []

        skills_str = ', '.join(skills[:15])

        prompt = f"""Create an interview preparation guide for:

ROLE: {role}
CANDIDATE SKILLS: {skills_str}
EXPERIENCE LEVEL: {experience_level}

Generate a comprehensive guide in JSON format:
{{
    "preparation_overview": {{
        "timeline": "Recommended preparation time",
        "focus_areas": ["Area 1", "Area 2", "Area 3"]
    }},
    "common_questions": [
        {{
            "question": "Interview question",
            "category": "Technical/Behavioral/Situational",
            "tips": "How to answer",
            "sample_answer_structure": "Brief framework for answering"
        }}
    ],
    "technical_preparation": {{
        "topics_to_review": ["Topic 1", "Topic 2"],
        "practice_resources": ["Free resource 1", "Free resource 2"]
    }},
    "behavioral_preparation": {{
        "star_method_reminder": "Brief STAR method explanation",
        "stories_to_prepare": [
            {{
                "scenario_type": "Leadership/Challenge/Failure/Success",
                "what_to_highlight": "Key points to mention"
            }}
        ]
    }},
    "questions_to_ask": [
        {{
            "question": "Question to ask interviewer",
            "why_ask": "What it shows about you"
        }}
    ],
    "day_of_tips": [
        "Tip 1",
        "Tip 2"
    ],
    "red_flags_to_avoid": [
        "Thing to avoid 1",
        "Thing to avoid 2"
    ]
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            guide = self._clean_json_response(response_text)
            return guide

        except Exception as e:
            print(f"Error generating interview prep: {e}")
            return {
                "preparation_overview": {
                    "timeline": "1-2 weeks recommended",
                    "focus_areas": ["Technical skills", "Behavioral questions", "Company research"]
                },
                "common_questions": [
                    {
                        "question": "Tell me about yourself",
                        "category": "Behavioral",
                        "tips": "Keep it professional and relevant to the role"
                    }
                ],
                "questions_to_ask": [
                    {
                        "question": "What does success look like in this role?",
                        "why_ask": "Shows you're goal-oriented"
                    }
                ]
            }

    def get_resume_enhancement_for_role(self, current_resume_data, target_role):
        """Get specific resume enhancement suggestions for a target role"""

        skills = current_resume_data.get('skills', [])
        if isinstance(skills, str):
            skills = json.loads(skills) if skills else []

        work_history = current_resume_data.get('work_history', [])
        if isinstance(work_history, str):
            work_history = json.loads(work_history) if work_history else []

        skills_str = ', '.join(skills[:15])

        prompt = f"""Analyze how to optimize this resume for the target role.

TARGET ROLE: {target_role}
CURRENT SKILLS: {skills_str}
EXPERIENCE COUNT: {len(work_history)} positions

Provide specific enhancement suggestions in JSON format:
{{
    "overall_assessment": {{
        "current_fit": "Percentage estimate",
        "main_gaps": ["Gap 1", "Gap 2"],
        "main_strengths": ["Strength 1", "Strength 2"]
    }},
    "keyword_optimization": {{
        "keywords_to_add": ["Keyword 1", "Keyword 2", "Keyword 3"],
        "keywords_to_emphasize": ["Already have but should highlight"],
        "ats_tips": ["ATS optimization tip"]
    }},
    "skills_section_optimization": {{
        "must_have_skills": ["Skill to add/highlight"],
        "nice_to_have_skills": ["Additional skills to consider"],
        "suggested_order": ["How to order skills section"]
    }},
    "summary_statement": {{
        "recommended_focus": "What to emphasize",
        "sample_opening": "Example opening line",
        "key_points_to_include": ["Point 1", "Point 2"]
    }},
    "format_suggestions": {{
        "recommended_sections": ["Section 1", "Section 2"],
        "length_recommendation": "1 page / 2 pages"
    }}
}}

Return ONLY valid JSON."""

        try:
            response_text = self._call_groq(prompt)
            suggestions = self._clean_json_response(response_text)
            return suggestions

        except Exception as e:
            print(f"Error generating resume enhancement: {e}")
            return {
                "overall_assessment": {
                    "current_fit": "Analysis unavailable",
                    "main_gaps": [],
                    "main_strengths": skills[:3] if skills else []
                },
                "keyword_optimization": {
                    "keywords_to_add": [],
                    "ats_tips": ["Use standard section headings", "Include relevant keywords from job description"]
                }
            }

    def _get_default_advice(self, domain, experience_level):
        """Return default advice when API fails"""
        return {
            "career_summary": {
                "current_standing": f"You are a {experience_level} level professional in {domain}",
                "strengths": ["Domain expertise", "Relevant experience"],
                "areas_for_growth": ["Continue skill development", "Build professional network"],
                "market_position": "Competitive in current market"
            },
            "recommended_roles": [
                {
                    "role_title": f"Senior {domain} Professional",
                    "match_reason": "Natural career progression",
                    "demand_level": "medium"
                }
            ],
            "immediate_actions": [
                {
                    "action": "Update your LinkedIn profile",
                    "timeline": "This week",
                    "impact": "high"
                },
                {
                    "action": "Identify skill gaps for target roles",
                    "timeline": "This month",
                    "impact": "high"
                }
            ],
            "skill_development_priority": [],
            "networking_advice": {
                "platforms": ["LinkedIn", "Industry-specific forums"],
                "tips": ["Engage with content in your field", "Connect with professionals in target companies"]
            },
            "long_term_vision": {
                "5_year_outlook": "Leadership or specialist role",
                "future_proof_skills": ["Adaptability", "Continuous learning"]
            }
        }


# Convenience functions for quick access

def get_career_advice(candidate_profile, target_role=None):
    """Quick function to get career advice"""
    advisor = CareerAdvisor()
    return advisor.get_career_advice(candidate_profile, target_role)


def get_role_roadmap(current_role, target_role, current_skills):
    """Quick function to get role transition roadmap"""
    advisor = CareerAdvisor()
    return advisor.get_role_roadmap(current_role, target_role, current_skills)


def get_industry_insights(domain):
    """Quick function to get industry insights"""
    advisor = CareerAdvisor()
    return advisor.get_industry_insights(domain)


def get_interview_prep(role, skills, experience_level):
    """Quick function to get interview preparation guide"""
    advisor = CareerAdvisor()
    return advisor.get_interview_preparation(role, skills, experience_level)
