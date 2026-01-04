import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=250, unique=True,verbose_name='username')
    is_admin = models.BooleanField(default=False, verbose_name="user is admin")
    
    objects=UserManager()
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return self.username

    @property
    def is_active(self) -> bool:
        return True
    
    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)


class ProfileModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username} - ({self.pk})"
    