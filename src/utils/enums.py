from enum import Enum

class LearningFormat(str, Enum):
    VIDEO = "Video Lectures"
    INTERACTIVE = "Interactive Exercises"
    TEXT = "Text-based Content"
    PROJECT = "Project-based Learning"
    BLENDED = "Blended Learning"

class ExperienceLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class CareerGoal(str, Enum):
    KNOWLEDGE = "Knowledge Acquisition"
    PROFESSIONAL = "Professional Development"
    CAREER = "Career Transition"
    ACADEMIC = "Academic Requirement" 