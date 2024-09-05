from django.contrib import admin

from waveview.feedback.models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "message",
        "created_at",
        "updated_at",
    )
