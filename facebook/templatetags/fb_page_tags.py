from django import template
from django.conf import settings
from django.utils.translation import ugettext as _
register = template.Library()
from django.utils.safestring import mark_safe

WEEK = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
VERBOSE_WEEKDAYS = (_('Mon'), _('Tue'), _('Wed'),
                    _('Thu'), _('Fri'), _('Sat'), _('Sun'))


WEEKDAYS = getattr(settings, 'WEEKDAYS', VERBOSE_WEEKDAYS)

@register.inclusion_tag('facebook/opening_hours.html')
def opening_hours(hours):
    """
    This tag prettifies the opening hours field for facebook places
    @param hours: the field of the facebook page.
    """
    from_day = WEEKDAYS[0]
    to_day = WEEKDAYS[0]
    o1, o2, c1, c2 = None, None, None, None
    result = u''

    for i in range(len(WEEK)):
        no1 = hours.get('%s_1_open' % WEEK[i], None)
        nc1 = hours.get('%s_1_close' % WEEK[i], None)
        no2 = hours.get('%s_2_open' % WEEK[i], None)
        nc2 = hours.get('%s_2_close' % WEEK[i], None)
        # first run and open mon
        if not (o1 or o2 or c1 or c2) and (no1 or no2):
            o1, o2, c1, c2 = no1, no2, nc1, nc2
            from_day = WEEKDAYS[i]
        elif not (o1 or o2 or c1 or c2):
            # beginning of the week and closed.
            continue

        # opening hours have not changed for the current day
        if no1 == o1 and no2 == o2 and nc1 == c1 and nc2 == c2 and no1:
            to_day = VERBOSE_WEEKDAYS[i]
        # opening hours have changed. Store and write out the previous days.
        else:
            if from_day == to_day:
                if o2:
                    result += u'%s: %s-%s %s-%s<br />' % (from_day, o1, c1, o2, c2)
                else:
                    result += u'%s: %s-%s<br />' % (from_day, o1, c1)
            else:
                if o2:
                    result += u'%s-%s: %s-%s %s-%s<br />' % (from_day, to_day, o1, c1, o2, c2)
                else:
                    result += u'%s-%s: %s-%s<br />' % (from_day, to_day, o1, c1)
            from_day = WEEKDAYS[i]
            to_day = WEEKDAYS[i]
            o1, o2, c1, c2 = no1, no2, nc1, nc2


    context = {'hours': mark_safe(result) }
    return context
