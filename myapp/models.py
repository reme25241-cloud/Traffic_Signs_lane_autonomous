# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models

class CustomUser(AbstractUser):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    def __str__(self):
        return f"{self.name})"

from django.conf import settings

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_group_message = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} to {self.receiver or 'Group'}"



# feedback models.py

from django.db import models
from django.conf import settings

class Feedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Feedback from {self.user.name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

# models.py mainApplicationFunctionality20240625


# models.py
from django.db import models

class SignUpload(models.Model):
    original_image = models.ImageField(upload_to="traffic_signs/original/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upload #{self.id}"

class SignPrediction(models.Model):
    upload = models.ForeignKey(SignUpload, on_delete=models.CASCADE, related_name="predictions")
    predicted_sign = models.CharField(max_length=100)
    confidence = models.FloatField(default=0.0)
    notes = models.TextField(blank=True, null=True)

    # derived images
    grayscale_image = models.ImageField(upload_to="traffic_signs/grayscale/", blank=True, null=True)
    blurred_image = models.ImageField(upload_to="traffic_signs/blurred/", blank=True, null=True)
    equalized_image = models.ImageField(upload_to="traffic_signs/equalized/", blank=True, null=True)
    thresholded_image = models.ImageField(upload_to="traffic_signs/thresholded/", blank=True, null=True)
    roi_image = models.ImageField(upload_to="traffic_signs/roi/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.predicted_sign} ({self.confidence:.2f}%)"
