from django.template.loader import render_to_string
from fcm_django.models import FCMDevice
from django.core.mail import get_connection as get_mail_connection, EmailMessage

from HRTool import utils, settings


class NotificationManager:

    @staticmethod
    def kra_setting_notification(request, kra):
        mail = render_to_string("kra/emails/setting.html", {
            "user": request.user.profile.manager.user,
            "kra": kra,
            'request': request
        })
        utils.send_mail('KRA Setting Notification', mail, request.user.profile.manager.user.email)
        devices = FCMDevice.objects.filter(user=request.user.profile.manager.user)
        if devices.exists():
            if request.user.profile.gender.lower() == "female":
                body = "{0}({1}) just submitted her KRA".format(request.user.get_full_name(), request.user.profile.auuid)
            else:
                body = "{0}({1}) just submitted his KRA".format(request.user.get_full_name(), request.user.profile.auuid)
            devices.send_message(title="KRA Notification", body=body)

    @staticmethod
    def kra_update_notification(request, kra):
        user = kra.user if request.user != kra.user else None
        if user is None and kra.user.profile.manager:
            user = kra.user.profile.manager.user
        if user:
            mail = render_to_string("kra/emails/kra-update.html", {
                "kra": kra,
                "request": request,
                "user": user
            })
            utils.send_mail('KRA Setting Notification', mail, user.email)
            devices = FCMDevice.objects.filter(user=user)
            if devices.exists():
                if user != kra.user:
                    body = "Hi! {0}({1}) just updated {2} KRA setting".format(kra.user.get_full_name(), kra.user.profile.auuid, "his" if kra.user.profile.gender.lower() == "male" else "her")
                else:
                    body = "Hi! You have an update on your KRA setting"
                devices.send_message(title="KRA Notification", body=body)

    @staticmethod
    def bucket_update_notification(request, bucket):
        mails = []
        users = []
        mail_connection = get_mail_connection()
        for member in bucket.company.members.all():
            users.append(member.user)
            content = render_to_string("kra/emails/bucket-update.html", {
                "bucket": bucket, "user": member.user,
                "request": request
            })
            mail_object = EmailMessage("KRA Setting Notification", content, settings.NOTIFICATION_SENDER,
                                       [member.user.email], connection=mail_connection)
            mail_object.content_subtype = "html"
            mails.append(mail_object)
        mail_connection.send_messages(mails)
        devices = FCMDevice.objects.filter(user__in=users)
        if devices.exists():
            body = "KRA Setting for %s is now " % bucket.title
            if bucket.status == 'Open' and bucket.allow_final_assessment:
                body += "open for final assessment"
            elif bucket.status == 'Open' and bucket.allow_self_assessment:
                body += "open for self assessment"
            elif bucket.status == 'Open':
                body += "open"
            else:
                body += "closed"
            devices.send_message(title="KRA Notification", body=body)

    @staticmethod
    def task_creation_notification(request, task):
        mail = render_to_string("task/emails/creation.html", {
            "user": task.assigned_to.user,
            "request": request
        })
        utils.send_mail("Task Notification", mail, [task.assigned_to.user.email])
        devices = FCMDevice.objects.filter(user=task.assigned_to.user)
        if devices.exists():
            devices.send_message(title="New Task Notification", body="Hi! {0}({1}) just assigned a task to you.".format(task.created_by.user.get_full_name(), task.created_by.auuid))

    @staticmethod
    def task_update_notification(request, task):
        user = task.assigned_to.user if task.assigned_to.user != request.user else task.created_by.user
        mail = render_to_string("task/emails/update.html", {
            "user": user,
            "request": request
        })
        utils.send_mail("Task Notification", mail, [user.email])
        devices = FCMDevice.objects.filter(user=user)
        if devices.exists():
            devices.send_message(title="Task Update Notification", body="Hi! You have an update on one of your tasks.")

    @staticmethod
    def pip_notification(request, user, pip):
        mail = render_to_string("pip/emails/creation.html", {
            "user": user,
            "request": request,
            'pip': pip
        })
        utils.send_mail("PIP Notification", mail, [user.email])
        devices = FCMDevice.objects.filter(user=user)
        if devices.exists():
            devices.send_message(title="PIP Notification", body="Hi! A PIP has been raised for you.")
