from django.contrib import admin
from vctasks.addtask.models import Task, Doc, Person, Module, TaskCategory,\
                                  NotificationEvent, GroupNotification, NotificationTemplate,\
                                  GroupNotificationTemplate


class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'notify_applicant', 'notify_manager', 'notify_developer')
    
admin.site.register(Task)
admin.site.register(Doc)
admin.site.register(Person)
admin.site.register(Module)
admin.site.register(TaskCategory)
admin.site.register(NotificationEvent, NotificationEventAdmin)
admin.site.register(GroupNotification)
admin.site.register(NotificationTemplate)
admin.site.register(GroupNotificationTemplate)


