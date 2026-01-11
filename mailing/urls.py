from django.urls import path
from mailing.apps import MailingConfig
from mailing.views import (HomeView, SubscriberListView, SubscriberDetailView, SubscriberCreateView,
                           SubscriberUpdateView, SubscriberDeleteView, MessageListView, MessageDetailView,
                           MessageCreateView, MessageUpdateView, MessageDeleteView, MailingModelListView,
                           MailingModelCreateView, MailingModelDetailView, MailingModelUpdateView,
                           MailingModelDeleteView, SendingMailingView, MailingAttemptListView,
                           DisableMailingView, MailingAttemptAllListView)

app_name = MailingConfig.name

urlpatterns = [
    path("home/", HomeView.as_view(), name="home"),
    path("subscribers/", SubscriberListView.as_view(), name="subscriber_list"),
    path("subscribers/<int:pk>/", SubscriberDetailView.as_view(), name="subscriber_detail"),
    path("subscribers/create/", SubscriberCreateView.as_view(), name="subscriber_create"),
    path("subscribers/<int:pk>/update/", SubscriberUpdateView.as_view(), name="subscriber_update"),
    path("subscribers/<int:pk>/delete/", SubscriberDeleteView.as_view(), name="subscriber_delete"),
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/<int:pk>/", MessageDetailView.as_view(), name="message_detail"),
    path("messages/create/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"),
    path("mailing/", MailingModelListView.as_view(), name="mailingmodel_list"),
    path("mailing/<int:pk>/", MailingModelDetailView.as_view(), name="mailingmodel_detail"),
    path("mailing/create", MailingModelCreateView.as_view(), name="mailingmodel_create"),
    path("mailing/<int:pk>/update/", MailingModelUpdateView.as_view(), name="mailingmodel_update"),
    path("mailing/<int:pk>/delete/", MailingModelDeleteView.as_view(), name="mailingmodel_delete"),
    path("mailing/<int:pk>/sending-mailing/", SendingMailingView.as_view(), name="sending_mailing"),
    path('mailing/<int:pk>/attempts/', MailingAttemptListView.as_view(), name='mailing_attempts'),
    path('mailing/<int:pk>/disable-mailing/', DisableMailingView.as_view(), name='disable_mailing'),
    path('mailing/attempt-list/', MailingAttemptAllListView.as_view(), name='attempt_list'),

]
