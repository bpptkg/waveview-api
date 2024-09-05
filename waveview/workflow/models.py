import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Workflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("workflow")
        verbose_name_plural = _("workflows")

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE, related_name="steps"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("workflow step")
        verbose_name_plural = _("workflow steps")
        unique_together = ("workflow", "order")

    def __str__(self):
        return self.name


class WorkflowStepTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    target = models.ForeignKey(
        WorkflowStep, on_delete=models.CASCADE, related_name="incoming_transitions"
    )
    condition = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("workflow step transition")
        verbose_name_plural = _("workflow step transitions")
        unique_together = ("source", "target")

    def __str__(self):
        return f"{self.source} -> {self.target}"


class WorkflowStepAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step = models.ForeignKey(
        WorkflowStep, on_delete=models.CASCADE, related_name="actions"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("workflow step action")
        verbose_name_plural = _("workflow step actions")

    def __str__(self):
        return self.name


class WorkflowStepActionParameter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.ForeignKey(
        WorkflowStepAction, on_delete=models.CASCADE, related_name="parameters"
    )
    name = models.CharField(max_length=255)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("workflow step action parameter")
        verbose_name_plural = _("workflow step action parameters")

    def __str__(self):
        return self.name
