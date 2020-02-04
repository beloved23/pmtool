import uuid

from django import forms
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

#
# def send_password_mail(email, password):
#     message = render_to_string('account/sign-up-email.html', context_dict)
#
#     send_mail(
#         'Subject',
#         'Use this password %s' % password,
#         'info@pat.tabtech.com.ng',
#         [email],
#     )
#
#
# def send_activation_mail(user, password):
#     send_mail(
#         'Subject',
#         'Use this link %s' % password,
#         'info@pat.tabtech.com.ng',
#         [user.email],
#     )
#
from HRTool import settings


def send_mail(subject, message, receiver):
    msg = EmailMessage(subject=subject, body=message, to=[receiver, ],
                       from_email=settings.NOTIFICATION_SENDER)
    msg.content_subtype = "html"
    return msg.send()


def random_string(string_length=8):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4())  # Convert UUID format to a Python string.
    random = random.lower()   # Make all characters uppercase.
    random = random.replace("-", "")    # Remove the UUID '-'.
    return random[0:string_length]  # Return the random string.


def build_response(success, message, data):
    return {
        "success": success,
        "message": message,
        "data": data
    }


def verify_attachments(self, cd, field):
    image = cd.get(field)
    # validate content type
    main, sub = image.content_type.split('/')
    if not (main == 'image' and sub in ['jpeg', 'pjpeg', 'png', 'jpg']):
        self.add_error(field, u'Please use a JPEG or PNG image')
    # if len(image) > (3 * 1024 * 1024):
    #     self.add_error(field, u'Image file size may not exceed 3MB')
    # issue = issue_type
    # if not issue:
    #     raise forms.ValidationError(u"Please, select an Issue Type")
    # empty_images = 1
    # if issue.image_upload:
    #     i = 1
    #     while i <= 4:
    #         field = "image{0}".format(i)
    #         if cd.has_key(field) and cd.get(field) is not None:
    #
    #         else:
    #             empty_images += 1
    #         i += 1

    # if issue.video_upload:
    #     video = cd.get('video_file', None)
    #     if video is not None:
    #         main, sub = video.content_type.split('/')
    #         if not (main in ["video"] and sub in ['mp4', 'avi', '3gp']):
    #             self.add_error("video_file", u'Please use an MP4 or AVI Video file')
    #         # if len(video) > (10 * 1024 * 1024):
    #         #     self.add_error("video_file", u'Video file size may not exceed 10MB')
    #     else:
    #         self.add_error("video_file", u"Video attachment cannot be empty for this issue type")
    # if empty_images > 4:
    #     raise forms.ValidationError(u"You must upload at least an Image file for this issue type")
