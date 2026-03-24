from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
	class UserRole(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		COMMON = 'COMMON', 'Usuario comum'

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.COMMON)

	def __str__(self):
		return f'{self.user.username} ({self.get_role_display()})'
