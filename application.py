"""
AWS Elastic Beanstalk entry point.

This file is required by Elastic Beanstalk and must be named 'application.py'.
Elastic Beanstalk looks for an 'application' variable by default.
"""

from app.main import app

# Elastic Beanstalk looks for 'application' variable by default
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)

