from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
#Models User
class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('pt', 'Personal Trainer'),
        ('member', 'Member'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='member')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Thêm related_name để tránh xung đột
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',  # Đổi tên reverse accessor
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Đổi tên reverse accessor
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    # Thêm REQUIRED_FIELDS để yêu cầu nhập khi tạo superuser
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'phone', 'role']
    def __str__(self):
        return self.username

from decimal import Decimal

#Models MemberProfile
class MemberProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # kg
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    goal = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_bmi(self):
        if self.height and self.weight and self.height > 0:  # Đảm bảo height > 0
            height_m = Decimal(self.height) / Decimal('100')  # Chuyển cm thành m
            bmi = Decimal(self.weight) / (height_m ** 2)
            return round(bmi, 2)
        return None

    def save(self, *args, **kwargs):
        self.bmi = self.calculate_bmi()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Profile of {self.user.username}"

#Models Packages
from django.core.validators import MinValueValidator
class Package(models.Model):
    PACKAGE_TYPE_CHOICES = (
        ('monthly', 'Monthly'),  # Tháng
        ('quarterly', 'Quarterly'),  # Quý
        ('yearly', 'Yearly'),  # Năm
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    pt_sessions = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # Số buổi với PT
    package_type = models.CharField(max_length=10, choices=PACKAGE_TYPE_CHOICES, default='monthly')  # Thêm default, quý, năm
    created_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='created_packages')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
from datetime import datetime, timedelta

class MemberPackage(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_packages', limit_choices_to={'role': 'member'})
    package = models.ForeignKey(Package, on_delete=models.RESTRICT, related_name='member_packages')
    start_date = models.DateField()
    end_date = models.DateField()
    remaining_sessions = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Tự động tính end_date khi tạo mới
        if not self.id:  # Chỉ tính khi tạo mới
            if self.package.package_type == 'monthly':
                self.end_date = self.start_date + timedelta(days=30)  # 1 tháng = 30 ngày
            elif self.package.package_type == 'quarterly':
                self.end_date = self.start_date + timedelta(days=90)  # 1 quý = 90 ngày
            elif self.package.package_type == 'yearly':
                self.end_date = self.start_date + timedelta(days=365)  # 1 năm = 365 ngày

            # Gán remaining_sessions
            self.remaining_sessions = self.package.pt_sessions

        # Tự động cập nhật status
        if self.end_date < datetime.now().date():
            self.status = 'expired'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"

#Models Schedules
class Schedule(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': 'member'}
    )
    pt = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pt_schedules',
        null=True,
        blank=True,
        limit_choices_to={'role': 'pt'}
    )
    member_package = models.ForeignKey(
        MemberPackage,
        on_delete=models.RESTRICT,
        related_name='schedules',
        null=True,
        blank=True
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Kiểm tra số buổi còn lại nếu đặt lịch với PT
        if self.pt and self.member_package:
            if self.member_package.remaining_sessions <= 0:
                raise ValueError("No remaining PT sessions in this package.")
            if self.status == 'approved' and self._state.adding is False:  # Chỉ giảm khi cập nhật status thành approved
                if self.__class__.objects.get(pk=self.pk).status != 'approved':  # Kiểm tra status trước đó
                    self.member_package.remaining_sessions -= 1
                    self.member_package.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.start_time}"

    class Meta:
        ordering = ['start_time']

#Models Progress
class Progress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_records',
        limit_choices_to={'role': 'member'}
    )
    pt = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pt_progress_records',
        null=True,
        blank=True,
        limit_choices_to={'role': 'pt'}
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)]
    )
    body_fat = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    muscle_mass = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    note = models.TextField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.recorded_at}"

    class Meta:
        ordering = ['recorded_at']

#Models Reveiw

class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        limit_choices_to={'role': 'member'}
    )
    pt = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pt_reviews',
        null=True,
        blank=True,
        limit_choices_to={'role': 'pt'}
    )
    gym_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    pt_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if not self.pt and self.pt_rating is not None:
            raise ValueError("pt_rating should be null when there is no PT.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Review by {self.user.username}"

#Models Payments
class Payment(models.Model):
    METHOD_CHOICES = (
        ('momo', 'MoMo'),
        ('vnpay', 'VNPAY'),
        ('bank', 'Bank Transfer'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    member_package = models.ForeignKey(MemberPackage, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    receipt_url = models.URLField(null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment {self.member_package} - {self.amount}"

#Models notification
class Notification(models.Model):
    TYPE_CHOICES = (
        ('reminder', 'Reminder'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

#Models chats
class Chat(models.Model):
    chat_name = models.CharField(max_length=100, null=True, blank=True)  # Tên nhóm (cho nhóm chat)
    is_group = models.BooleanField(default=False)  # Phân biệt chat 1-1 và nhóm
    last_message = models.TextField(null=True, blank=True)  # Lưu tin nhắn cuối (cache)
    last_updated = models.DateTimeField(auto_now=True)  # Thời gian cập nhật
    firebase_chat_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Liên kết với Firebase

    def __str__(self):
        return self.chat_name or f"Chat {self.id}"

class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_participants')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('chat', 'user')  # Đảm bảo không trùng user trong cùng chat

    def __str__(self):
        return f"{self.user.username} in {self.chat}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    firebase_message_id = models.CharField(max_length=100, unique=True, null=True, blank=True)  # Liên kết với Firebase

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
