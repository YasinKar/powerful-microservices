from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager
from django.core.validators import RegexValidator


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=250, unique=True,verbose_name='your username')
    is_staff = models.BooleanField(default=False, verbose_name="user is active")
    is_admin = models.BooleanField(default=False, verbose_name="user is admin")
    
    objects=UserManager()
    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return self.username
        
    @property
    def is_staff(self) -> bool:
        return self.is_staff

    @property
    def is_active(self) -> bool:
        return True
    
    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)


class ProfileModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250, null=True, blank=True)
    code = models.PositiveBigIntegerField()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,11}$', message="Phone number must be entered in the format: '09129876543'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=11, null=True, blank=True) # Validators should be a list
    date = models.DateField()
    title = models.CharField(max_length=250)
    code_id = models.PositiveBigIntegerField()

    def __str__(self) -> str:
        return f"{self.user.username} - ({self.pk})"
    