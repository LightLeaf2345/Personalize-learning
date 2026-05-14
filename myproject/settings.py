# myproject/settings.py (chỉ phần liên quan cần đảm bảo tồn tại / chỉnh)
from pathlib import Path
import os
from environ import Env
# BASE_DIR (thường có sẵn trong Django 3.1+ templates)
BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()
Env.read_env(os.path.join(BASE_DIR, '.env'))

# PHẢI CÓ 2 DÒNG NÀY
GEMINI_API_KEY = env("GEMINI_API_KEY")
SERPAPI_API_KEY = env("SERPAPI_API_KEY", default="")
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "replace-this-with-your-secret-key"

# DEBUG (True cho dev)
DEBUG = True

ALLOWED_HOSTS = []

# ------------------------
# INSTALLED_APPS
# ------------------------
INSTALLED_APPS = [
    # django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # your apps
    'import_export',
    "learning",   
]

# ------------------------
# MIDDLEWARE (giữ mặc định)
# ------------------------
MIDDLEWARE = [
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "myproject.urls"

# ------------------------
# TEMPLATES
# ------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [ BASE_DIR / "templates" ],
        "APP_DIRS": True, 
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"

# ------------------------
# DATABASE (mặc định sqlite cho dev)
# ------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ------------------------
# PASSWORD VALIDATORS (mặc định hoặc tùy chỉnh)
# ------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ------------------------
# I18N / TIMEZONE - giữ mặc định hoặc điều chỉnh
# ------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ------------------------
# STATIC FILES
# ------------------------
STATIC_URL = "/static/"
# thư mục chứa static files ở cấp project nếu cần (khi develop)
STATICFILES_DIRS = [
    BASE_DIR / "static",               # optional: project-level static
]
# nơi collectstatic gom vào (production)
STATIC_ROOT = BASE_DIR / "staticfiles"

# ------------------------
# Login/Logout redirects (dùng auth built-in views)
# ------------------------
LOGIN_REDIRECT_URL = "/"   # sau login sẽ về trang home
LOGOUT_REDIRECT_URL = "/"  # sau logout
# ------------------------

# (Các cấu hình khác: EMAIL, LOGGING, v.v... giữ nguyên)

CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://unpkg.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")

# Session hết hạn sau 1 ngày (đơn vị: giây)
SESSION_COOKIE_AGE = 86400 
# Lưu session vào database ngay khi có thay đổi
SESSION_SAVE_EVERY_REQUEST = True

STATICFILES_DIRS = [ BASE_DIR / "static" ]