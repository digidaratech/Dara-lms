from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class User:
    id: int
    name: str
    email: str
    mobile: str
    password_hash: str
    created_at: datetime
    enrolled_courses: List[int] = None
    
    def __post_init__(self):
        if self.enrolled_courses is None:
            self.enrolled_courses = []

@dataclass
class Course:
    id: int
    title: str
    description: str
    instructor: str
    duration: str
    price: float
    modules: List[str]
    video_urls: List[str] = None
    materials: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.video_urls is None:
            self.video_urls = []
        if self.materials is None:
            self.materials = []

@dataclass
class Enrollment:
    user_id: int
    course_id: int
    enrolled_at: datetime
    login_id: str
    course_password: str
