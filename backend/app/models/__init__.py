"""Import all models so SQLAlchemy's relationship() string-references resolve.

Any code that uses the ORM (web server, Celery worker, tests) imports this
package transitively, ensuring every model class is registered in the
mapper registry before string-based `relationship("OtherModel", ...)`
expressions are evaluated.
"""
from app.models.profile import UserProfile  # noqa: F401
from app.models.job import Job, JobRequirement, JobScore  # noqa: F401
from app.models.resume import ResumeVariant  # noqa: F401
from app.models.asset import ApplicationAsset  # noqa: F401
from app.models.outreach import Outreach  # noqa: F401
from app.models.interview import Interview  # noqa: F401
from app.models.settings import UserSettings  # noqa: F401
from app.models.application import ApplicationAttempt  # noqa: F401
