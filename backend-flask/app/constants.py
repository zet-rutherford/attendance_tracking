# Status codes
STATUS_CODE_SUCCESS = 200
STATUS_CODE_BAD_REQUEST = 400
STATUS_CODE_UNAUTHORIZED = 401
STATUS_CODE_FORBIDDEN = 403
STATUS_CODE_NOT_FOUND = 404
STATUS_CODE_SERVER_ERROR = 500

# Error messages
USER_NOT_FOUND = 'user.not.found'
FACE_NOT_FOUND = 'face.not.found'
INVALID_FACE = 'invalid.face'
FACE_VERIFICATION_FAILED = 'face.verification.failed'
INVALID_CREDENTIALS = 'invalid.credentials'
USERNAME_EXISTS = 'username.already.exists'

# Check-in/out status
CHECK_STATUS_ON_TIME = 'on_time'
CHECK_STATUS_LATE = 'late'
CHECK_STATUS_EARLY = 'early'

# User status
USER_STATUS_ACTIVE = 1
USER_STATUS_INACTIVE = 0

# File upload
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Face verification
FACE_SIMILARITY_THRESHOLD = 0.85  # Minimum similarity score for face verification
MAX_FEATURE_COUNT = 5    # Maximum number of face features per user

# Attendance rules
LATE_THRESHOLD_MINUTES = 15  # Minutes after schedule to be marked as late
EARLY_LEAVE_THRESHOLD_MINUTES = 15  # Minutes before schedule to be marked as early leave

# JWT settings
JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = 30 * 24 * 60 * 60  # 30 days

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 60
MAX_FAILED_LOGIN_ATTEMPTS = 5
FAILED_LOGIN_TIMEOUT = 300  # 5 minutes