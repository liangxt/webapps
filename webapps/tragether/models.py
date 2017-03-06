from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Max
from django.utils import timezone
from django.utils.html import escape
from vote.managers import VotableManager

from tragether.choice import *
import sys
import pytz

from django.contrib.staticfiles.templatetags.staticfiles import static


def default_time():
    return timezone.now() + timezone.timedelta(+1)


class Travel(models.Model):
    creator = models.ForeignKey(User, null=True)
    destination = models.CharField(max_length=40)
    group_size = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_time = models.DateTimeField(default=timezone.datetime.today())
    end_time = models.DateTimeField(default=default_time())
    budget = models.FloatField(validators=[MinValueValidator(0.0),
                                           MaxValueValidator(sys.float_info.max)])
    info = models.CharField(max_length=420)
    status = models.CharField(max_length=1, choices=STATUSCHOICE, default="1")

    def __unicode__(self):
        return self.destination

    def __str__(self):
        return self.destination

    @property
    def get_members(self):
        lst = []
        for member in self.member.all():
            lst.append(member.user)
        return lst

    @property
    def get_applied_users(self):
        lst = []
        for applied_msg in self.travel_applied_message.filter(applied=True, read_status=False):
            lst.append(applied_msg.sender)
        return lst

    @property
    def get_invited_users(self):
        lst = []
        for invited_msg in self.travel_applied_message.filter(applied=False, read_status=False):
            lst.append(invited_msg.receiver)
        return lst


def upload_to_func(instance, filename):
    return 'photos/%s' % instance.user.username


class Person(models.Model):
    user = models.OneToOneField(User)
    age = models.IntegerField(null=True, blank=True,
                              validators=[MinValueValidator(0), MaxValueValidator(125)])
    bio = models.CharField(max_length=420, default="", blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    picture = models.ImageField(upload_to=upload_to_func, blank=True)
    travel_in = models.ManyToManyField(Travel, related_name='member')

    def __unicode__(self):
        return self.user.username

    def __str__(self):
        return self.user.username

    @property
    def get_pic_url(self):
        if not self.picture:
            return static('tragether/image/photo_holder.jpg')
        return self.picture.url


class Chatbox_Messages(models.Model):
    travel = models.ForeignKey(Travel)
    sender = models.ForeignKey(User)
    content = models.CharField(max_length=420)
    datetime = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.content

    def __str__(self):
        return self.content

    @property
    def get_photo_url(self):
        person = Person.objects.get(user=self.sender)
        return person.get_pic_url

    @property
    def html(self):
        return "<div class='row row-msg'>\
        <div class='col-md-2 col-xs-2 msg-text-photo'>\
        <img src='%s' alt=' %s' class='img-responsive'>\
        </div>\
        <div class='col-md-10 col-xs-10 msg-text-photo'>\
        <div class='messages'>\
        <p class='msg-content'>%s</p>\
        <p class='msg-time-user'>%s from %s</p>\
        </div></div></div>" % (self.get_photo_url, \
            self.sender, escape(self.content), \
            self.datetime.astimezone(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M:%S"), \
            self.sender)


class Itinerary(models.Model):
    deleted = models.BooleanField(default=False)
    last_changed = models.DateTimeField(auto_now=True)
    travel = models.ForeignKey(Travel)
    place = models.CharField(max_length=420)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    start_time = models.DateTimeField()


    def __unicode__(self):
        return self.place
        
    def __str__(self):
        return self.__unicode__()

    @property
    def get_start_time(self):
        return self.start_time.astimezone(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M")

    @property
    def html(self):
        return "<tr id='itinerary_%d'><td>%s</td><td>%s</td><td id='%d'>\
        <a class='btn btn-info btn-xs itinerary-edit-delete-icon btn-itinerary-edit'><span class='glyphicon glyphicon-edit'></span></a><a class='btn btn-danger btn-xs itinerary-edit-delete-icon btn-itinerary-delete'><span class='glyphicon glyphicon-remove'></span></a>\
        </td></tr>" % (self.id, self.start_time.astimezone(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d %H:%M"), \
            escape(self.place), self.id)

    @staticmethod
    def get_max_time(travel):
        return Itinerary.objects.filter(travel=travel).aggregate(Max('last_changed'))['last_changed__max'] or "1970-01-01T00:00+00:00"

    @staticmethod
    def get_itineraries(travel):
        return Itinerary.objects.filter(travel=travel, deleted=False).distinct().order_by('start_time')

    @staticmethod
    def update_itineraries(travel, time="1970-01-01T00:00+00:00"):
        return Itinerary.objects.filter(travel=travel, last_changed__gt=time).distinct().order_by('start_time')


class ApplyInviteMsg(models.Model):
    travel = models.ForeignKey(Travel, related_name='travel_applied_message')
    sender = models.ForeignKey(User, related_name='sender')
    receiver = models.ForeignKey(User, related_name='receiver')
    datetime = models.DateTimeField(default=timezone.datetime)
    subject = models.CharField(max_length=42, blank=True)
    content = models.CharField(max_length=2048)
    read_status = models.BooleanField(default=False)
    accept_status = models.BooleanField(default=False)
    applied = models.BooleanField(default=True)

    def __unicode__(self):
        return self.travel.destination

    def __str__(self):
        return self.travel.destination


class Attraction(models.Model):
    name = models.CharField(max_length=30)
    votes = VotableManager()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Poll(models.Model):
    travel = models.OneToOneField(Travel)
    attraction = models.ManyToManyField(Attraction)

    def __unicode__(self):
        return self.travel.destination

    def __str__(self):
        return self.travel.destination
