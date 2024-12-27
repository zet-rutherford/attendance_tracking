import bcrypt
from app.extensions import db
from app.models.user import User

class UserService:
    def create_user(self, username, password, email, fullname, phone=None):
        """Create a new user with hashed password."""
        hashed_password = self.hash_password(password)
        
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            fullname=fullname,
            phone=phone
        )
        
        db.session.add(user)
        db.session.commit()
        return user
    
    def get_user_by_id(self, user_id):
        """Get user by ID."""
        return User.query.get(user_id)
    
    def get_user_by_username(self, username):
        """Get user by username."""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed_password):
        """Verify a password against a hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def update_user(self, user_id, **kwargs):
        """Update user attributes."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        for key, value in kwargs.items():
            if hasattr(user, key):
                if key == 'password':
                    value = self.hash_password(value)
                setattr(user, key, value)
                
        db.session.commit()
        return user
    
    def deactivate_user(self, user_id):
        """Deactivate a user account."""
        return self.update_user(user_id, active=False)
    
    def activate_user(self, user_id):
        """Activate a user account."""
        return self.update_user(user_id, active=True)