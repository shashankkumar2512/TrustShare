"""
Password Strength Validator Module — TrustShare Security

Industry-grade password validation with:
- Multiple strength requirements
- Common password detection
- Personalized password checks
- Password strength scoring
- Detailed feedback
- OWASP recommendations

References:
- NIST SP 800-63B (Digital Identity Guidelines)
- OWASP Authentication Cheat Sheet
- HaveIBeenPwned database (for common passwords)
"""

import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# CONFIGURATION

# Password requirements (industry standard)
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_STRENGTH_SCORE = 60  # Out of 100

# Common weak passwords (top 100 most common)
COMMON_PASSWORDS = {
    "password", "123456", "password123", "admin", "qwerty",
    "letmein", "welcome", "monkey", "dragon", "master",
    "iloveyou", "abc123", "111111", "password1", "1234567",
    "12345678", "12345", "1234", "123", "sunshine",
    "princess", "football", "shadow", "michael", "computer",
    "jesus", "ninja", "mustang", "access", "batman",
    "trustno1", "hello", "hunter", "buster", "soccer",
    "harley", "andrew", "tigger", "jordan", "michelle",
    "loveme", "banana", "asdfgh", "asdf", "1q2w3e4r",
    "zxcvbnm", "qazwsx", "1qaz2wsx", "abcdef", "starwars",
    "master", "letmein123", "password12", "welcome123",
    "admin123", "root", "toor", "pass", "test", "guest",
    "user", "test123", "demo", "sample", "temp", "temp123",
}

# Character patterns
UPPERCASE_PATTERN = re.compile(r'[A-Z]')
LOWERCASE_PATTERN = re.compile(r'[a-z]')
DIGIT_PATTERN = re.compile(r'\d')
SPECIAL_CHAR_PATTERN = re.compile(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]')

# Sequential patterns
SEQUENTIAL_PATTERNS = [
    "0123456789",
    "abcdefghijklmnopqrstuvwxyz",
    "qwertyuiopasdfghjklzxcvbnm",
]

# Public API
__all__ = [
    'PasswordStrength',
    'PasswordValidationResult',
    'validate_password',
    'get_password_strength',
    'is_password_strong_enough',
    'suggest_strong_password',
    'MIN_PASSWORD_LENGTH',
    'MIN_STRENGTH_SCORE',
]


# ENUMS & DATA CLASSES

class PasswordStrength(str, Enum):
    """Password strength levels."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class PasswordValidationResult:
    """Detailed password validation result."""
    is_valid: bool
    score: int  # 0-100
    strength: PasswordStrength
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    meets_requirements: Dict[str, bool] = field(default_factory=dict)
    estimated_crack_time: str = ""


# MAIN VALIDATION FUNCTION

def validate_password(
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    strict: bool = True,
    db=None
) -> PasswordValidationResult:
    """
    Comprehensive password strength validation.
    
    Args:
        password: Password to validate.
        username: Optional username (checks password doesn't contain it).
        email: Optional email (checks password doesn't contain it).
        strict: If True, require higher strength (default: True).
        
    Returns:
        PasswordValidationResult with detailed analysis.
        
    Example:
        >>> result = validate_password("MyP@ssw0rd123")
        >>> result.is_valid
        True
        >>> result.strength
        <PasswordStrength.STRONG: 'strong'>
    """
    issues = []
    suggestions = []
    meets_requirements = {}
    
    # Basic validation
    if not password:
        return PasswordValidationResult(
            is_valid=False,
            score=0,
            strength=PasswordStrength.VERY_WEAK,
            issues=["Password cannot be empty"],
            suggestions=["Please enter a password"],
        )
    
    if not isinstance(password, str):
        return PasswordValidationResult(
            is_valid=False,
            score=0,
            strength=PasswordStrength.VERY_WEAK,
            issues=["Password must be a string"],
        )
    
    # Length check
    length = len(password)
    meets_requirements['min_length'] = length >= MIN_PASSWORD_LENGTH
    meets_requirements['max_length'] = length <= MAX_PASSWORD_LENGTH
    
    if length < MIN_PASSWORD_LENGTH:
        issues.append(f"Too short (minimum {MIN_PASSWORD_LENGTH} characters)")
        suggestions.append(f"Add at least {MIN_PASSWORD_LENGTH - length} more characters")
    
    if length > MAX_PASSWORD_LENGTH:
        issues.append(f"Too long (maximum {MAX_PASSWORD_LENGTH} characters)")
    
    # Character type checks
    has_uppercase = bool(UPPERCASE_PATTERN.search(password))
    has_lowercase = bool(LOWERCASE_PATTERN.search(password))
    has_digit = bool(DIGIT_PATTERN.search(password))
    has_special = bool(SPECIAL_CHAR_PATTERN.search(password))
    
    meets_requirements['has_uppercase'] = has_uppercase
    meets_requirements['has_lowercase'] = has_lowercase
    meets_requirements['has_digit'] = has_digit
    meets_requirements['has_special'] = has_special
    
    if not has_uppercase:
        issues.append("Missing uppercase letters (A-Z)")
        suggestions.append("Add at least one uppercase letter")
    
    if not has_lowercase:
        issues.append("Missing lowercase letters (a-z)")
        suggestions.append("Add at least one lowercase letter")
    
    if not has_digit:
        issues.append("Missing numbers (0-9)")
        suggestions.append("Add at least one number")
    
    if not has_special:
        issues.append("Missing special characters (!@#$%^&*)")
        suggestions.append("Add at least one special character")
    
    # Common password check
    password_lower = password.lower()
    is_common = password_lower in COMMON_PASSWORDS
    meets_requirements['not_common'] = not is_common
    
    if is_common:
        issues.append("This is a commonly used password")
        suggestions.append("Choose a more unique password")
    
    # Sequential pattern check
    has_sequential = _check_sequential_patterns(password_lower)
    meets_requirements['no_sequential'] = not has_sequential
    
    if has_sequential:
        issues.append("Contains sequential characters (like 'abc' or '123')")
        suggestions.append("Avoid sequential characters")
    
    # Repeated character check
    has_repeated = _check_repeated_characters(password)
    meets_requirements['no_repeated'] = not has_repeated
    
    if has_repeated:
        issues.append("Contains too many repeated characters")
        suggestions.append("Vary your characters more")
    
    # Username/email check
    if username and len(username) >= 3:
        if username.lower() in password_lower:
            issues.append("Password contains your username")
            suggestions.append("Don't include your username in password")
            meets_requirements['no_username'] = False
        else:
            meets_requirements['no_username'] = True
    
    if email and '@' in email:
        email_part = email.split('@')[0].lower()
        if len(email_part) >= 3 and email_part in password_lower:
            issues.append("Password contains part of your email")
            suggestions.append("Don't include your email in password")
            meets_requirements['no_email'] = False
        else:
            meets_requirements['no_email'] = True
    
    # Calculate strength score
    score = _calculate_password_score(
        password,
        length,
        has_uppercase,
        has_lowercase,
        has_digit,
        has_special,
        is_common,
        has_sequential,
        has_repeated,
    )
    
    # Determine strength level
    strength = _score_to_strength(score)
    
    # Determine if valid
    threshold = MIN_STRENGTH_SCORE if strict else 40
    is_valid = (
        score >= threshold
        and length >= MIN_PASSWORD_LENGTH
        and length <= MAX_PASSWORD_LENGTH
        and not is_common
    )
    
    # Estimate crack time
    estimated_crack_time = _estimate_crack_time(score, length)
    
    return PasswordValidationResult(
        is_valid=is_valid,
        score=score,
        strength=strength,
        issues=issues,
        suggestions=suggestions,
        meets_requirements=meets_requirements,
        estimated_crack_time=estimated_crack_time,
    )

# HELPER FUNCTIONS

def _check_sequential_patterns(password: str, min_length: int = 3) -> bool:
    """Check for sequential character patterns."""
    for pattern in SEQUENTIAL_PATTERNS:
        for i in range(len(pattern) - min_length + 1):
            substr = pattern[i:i + min_length]
            if substr in password:
                return True
    return False


def _check_repeated_characters(password: str, max_repeated: int = 3) -> bool:
    """Check for too many repeated characters."""
    for i in range(len(password) - max_repeated + 1):
        if password[i] * max_repeated == password[i:i + max_repeated]:
            return True
    return False


def _calculate_password_score(
    password: str,
    length: int,
    has_upper: bool,
    has_lower: bool,
    has_digit: bool,
    has_special: bool,
    is_common: bool,
    has_sequential: bool,
    has_repeated: bool,
) -> int:
    """Calculate password strength score (0-100)."""
    score = 0
    
    # Length scoring (up to 40 points)
    if length >= MIN_PASSWORD_LENGTH:
        score += 20
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10
    
    # Character variety (up to 40 points)
    if has_upper:
        score += 10
    if has_lower:
        score += 10
    if has_digit:
        score += 10
    if has_special:
        score += 10
    
    # Complexity bonus (up to 20 points)
    unique_chars = len(set(password))
    if unique_chars >= 8:
        score += 10
    if unique_chars >= 12:
        score += 10
    
    # Penalties
    if is_common:
        score -= 50
    if has_sequential:
        score -= 15
    if has_repeated:
        score -= 10
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))


def _score_to_strength(score: int) -> PasswordStrength:
    """Convert numeric score to strength level."""
    if score >= 90:
        return PasswordStrength.VERY_STRONG
    elif score >= 75:
        return PasswordStrength.STRONG
    elif score >= 60:
        return PasswordStrength.GOOD
    elif score >= 40:
        return PasswordStrength.FAIR
    elif score >= 20:
        return PasswordStrength.WEAK
    else:
        return PasswordStrength.VERY_WEAK


def _estimate_crack_time(score: int, length: int) -> str:
    """Estimate password crack time (rough approximation)."""
    if score < 30:
        return "Less than a second"
    elif score < 50:
        return "A few minutes"
    elif score < 70:
        return "Several hours to days"
    elif score < 85:
        return "Several months to years"
    else:
        return "Centuries or more"


# CONVENIENCE FUNCTIONS

def get_password_strength(password: str) -> PasswordStrength:
    """Quick check for password strength level."""
    result = validate_password(password, strict=False)
    return result.strength


def is_password_strong_enough(password: str, strict: bool = True) -> bool:
    """Simple boolean check if password is acceptable."""
    result = validate_password(password, strict=strict)
    return result.is_valid


def suggest_strong_password(length: int = 16) -> str:
    """
    Suggest a strong random password.
    
    Args:
        length: Desired password length (default 16).
        
    Returns:
        Strong random password.
    """
    import secrets
    import string
    
    if length < MIN_PASSWORD_LENGTH:
        length = MIN_PASSWORD_LENGTH
    if length > MAX_PASSWORD_LENGTH:
        length = MAX_PASSWORD_LENGTH
    
    # Ensure at least one of each required character type
    chars = []
    chars.append(secrets.choice(string.ascii_uppercase))
    chars.append(secrets.choice(string.ascii_lowercase))
    chars.append(secrets.choice(string.digits))
    chars.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    # Fill rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    for _ in range(length - 4):
        chars.append(secrets.choice(all_chars))
    
    # Shuffle
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)