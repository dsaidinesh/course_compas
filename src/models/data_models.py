from dataclasses import dataclass
from ..utils.enums import LearningFormat, ExperienceLevel, CareerGoal

@dataclass
class UserPreferences:
    name: str
    subject: str
    availability: str
    budget: int
    format: LearningFormat
    experience: ExperienceLevel
    goal: CareerGoal 