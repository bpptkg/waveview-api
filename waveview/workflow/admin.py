from django.contrib import admin

from waveview.workflow.models import (
    Workflow,
    WorkflowStep,
    WorkflowStepAction,
    WorkflowStepActionParameter,
    WorkflowStepTransition,
)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "workflow",
        "order",
        "created_at",
        "updated_at",
    )


@admin.register(WorkflowStepTransition)
class WorkflowStepTransitionAdmin(admin.ModelAdmin):
    list_display = (
        "source",
        "target",
        "condition",
        "created_at",
        "updated_at",
    )


@admin.register(WorkflowStepAction)
class WorkflowStepActionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "step",
        "created_at",
        "updated_at",
    )


@admin.register(WorkflowStepActionParameter)
class WorkflowStepActionParameterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "value",
        "action",
        "created_at",
        "updated_at",
    )
