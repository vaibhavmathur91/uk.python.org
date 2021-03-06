import datetime
import re

from django.db import models
from django_amber.models import ModelWithContent, ModelWithoutContent, PagesManager


class UserGroup(ModelWithoutContent):
    name = models.CharField(max_length=255)
    url = models.URLField(null=True)

    dump_dir_path = 'user-groups'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    class Manager(PagesManager):
        def no_events_scheduled(self, year, month):
            subquery = self.filter(events__date__year=year, events__date__month=month)
            return self.exclude(id__in=subquery)

    objects = Manager()

    def future_events(self):
        today = datetime.date.today()
        return self.events.filter(date__gte=today)

    def past_events(self):
        today = datetime.date.today()
        return self.events.filter(date__lt=today)

    def next_event(self):
        upcoming_events = self.future_events()
        if upcoming_events:
            return upcoming_events[0]
        else:
            return None

    def other_future_events(self):
        today = datetime.date.today()
        sixty_days_time = today + datetime.timedelta(days=60)
        return self.future_events().filter(date__lte=sixty_days_time)[1:]


class Event(ModelWithoutContent):
    user_group = models.ForeignKey(UserGroup, related_name='events')
    name = models.CharField(max_length=255)
    url = models.URLField(null=True)
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    venue = models.CharField(max_length=255, null=True)

    dump_dir_path = 'events'
    key_structure = '[user_group]/[date]'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['date', 'time']

    class Manager(PagesManager):
        def scheduled_in_month(self, year, month):
            return self.filter(date__year=year, date__month=month)

        def future_events(self):
            today = datetime.date.today()
            return self.filter(date__gte=today)

        def future_events_in_next_month(self):
            today = datetime.date.today()
            thirty_days_time = today + datetime.timedelta(days=30)
            return self.filter(date__gte=today, date__lt=thirty_days_time)

    objects = Manager()


class NewsItem(ModelWithContent):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    date = models.DateField()
    newsletter_month = models.CharField(max_length=7, null=True)
    newsletter_only = models.BooleanField(default=False)

    dump_dir_path = 'news'

    @classmethod
    def fields_from_key(cls, key):
        pattern = '(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)-(?P<slug>.+)'
        match = re.match(pattern, key)
        groups = match.groupdict()
        date = datetime.datetime(int(groups['year']), int(groups['month']), int(groups['day']))
        return {'date': date, 'slug': groups['slug']}

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date']

    class Manager(PagesManager):
        def for_newsletter(self, year, month):
            newsletter_month = '{}-{:02d}'.format(year, month)
            return self.filter(newsletter_month=newsletter_month)

        def for_website(self, num_items=None):
            qs = self.filter(newsletter_only=False)
            if num_items is not None:
                qs = qs[:num_items]
            return qs

    objects = Manager()


class Sponsor(ModelWithoutContent):
    name = models.CharField(max_length=255)
    url = models.URLField(null=True)

    dump_dir_path = 'sponsors'


class SponsoredNewsItem(ModelWithContent):
    sponsor = models.ForeignKey(Sponsor)
    date = models.DateField()
    newsletter_month = models.CharField(max_length=7, null=True)

    dump_dir_path = 'sponsored-news'

    @classmethod
    def fields_from_key(cls, key):
        pattern = '(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)-(?P<sponsor>.+)'
        match = re.match(pattern, key)
        groups = match.groupdict()
        date = datetime.datetime(int(groups['year']), int(groups['month']), int(groups['day']))
        return {'date': date, 'sponsor': groups['sponsor']}

    class Manager(PagesManager):
        def for_newsletter(self, year, month):
            newsletter_month = '{}-{:02d}'.format(year, month)
            return self.filter(newsletter_month=newsletter_month)

    objects = Manager()


class Page(ModelWithContent):
    title = models.CharField(max_length=255)

    dump_dir_path = 'pages'

    def __str__(self):
        return self.title
