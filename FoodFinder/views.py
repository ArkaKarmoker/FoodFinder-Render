from django.shortcuts import render
from django.http import HttpResponse

from vendor.models import Vendor

from django.db.models import F, Func, FloatField, Value

class LLEarth(Func):
    function = 'll_to_earth'
    output_field = FloatField()

class EarthDistance(Func):
    function = 'earth_distance'
    output_field = FloatField()


def get_or_set_current_location(request):
    if 'lat' in request.session:
        lat = request.session['lat']
        lng = request.session['lng']
        return lng, lat
    elif 'lat' in request.GET:
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        request.session['lat'] = lat
        request.session['lng'] = lng
        return lng, lat
    else:
        return None


def home(request):
    if get_or_set_current_location(request) is not None:
        lng, lat = get_or_set_current_location(request)
        radius_meters = 1000 * 1000 # 1000 km radius

        vendors = Vendor.objects.filter(is_approved=True, user__is_active=True).select_related('user', 'user_profile').annotate(
            distance_meters=EarthDistance(
                LLEarth(Value(float(lat)), Value(float(lng))),
                LLEarth(F('user_profile__latitude'), F('user_profile__longitude'))
            )
        ).filter(distance_meters__lte=radius_meters).order_by("distance_meters")

        for v in vendors:
            v.kms = round(v.distance_meters / 1000.0, 1) if v.distance_meters is not None else 0
    else:
        vendors = Vendor.objects.filter(is_approved=True, user__is_active=True).select_related('user', 'user_profile')[:8]
    context = {
        'vendors': vendors,
    }
    return render(request, 'home.html', context)