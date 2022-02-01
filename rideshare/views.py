from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.views import generic
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import DateTimeField
from django.urls import reverse_lazy
from django.template.defaulttags import register
from django.contrib.messages.views import SuccessMessageMixin
from .forms import EditProfileForm, DriverProfileForm, UserProfileForm, RideRequestForm
from .models import UserProfile, OwnerRide, SharerRide, VehicleTypeInfo, User


@register.filter
def get_2D_list_value(mylist, key):
    return mylist[key][1]


# minus one for driver
@register.filter
def get_capacity(mylist, key):
    return mylist[key] - 1


# Create your views here.
def edit_ride_success_view(request, *args, **kwargs):
    ride = OwnerRide.objects.get(pk=kwargs['pk'])
    subject='Joined Ride Cancellation -- Ride Sharing Service'
    message='email content'
    from_email=settings.EMAIL_HOST_USER
    fail_silently=False
    html_message="\
    <h2>The following ride you joined has been <b>edited</b> by the ride owner recently.</h2>\
    <h3>Now the ride info is:</h3>\
    <p>Ride Id: %s</br>\
    Destination Address: %s</br>\
    Arrival Time: %s</br>\
    Number of owner part passengers: %s</p></br></br>\
    <h3>Because of the change, your sharer position has been cancelled.</br>\
    Sorry about this inconvenience, please search for another suitable open ride as soon as possible.\
    </h3>\
    " % (ride.pk, ride.destaddr, ride.arrivalTime, ride.numPassengers)
    recipient_list = [sharer.user.email for sharer in ride.sharerride_set.all()]

    if (len(recipient_list) > 0):
        # cancel all sharers
        for sharer in ride.sharerride_set.all():
            sharer.delete()
        # send notification email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
            html_message=html_message
        )
        info = "Edit Successfully.</br>Since you've edited the ride, all your ride sharer has been cancelled and notified via email."
    else:
        info = "Edit Successfully."
    context = {"info": info}
    return render(request, "rideshare/edit_ride_success.html", context=context)


def mark_complete_view(request, *args, **kwargs):
    ride = OwnerRide.objects.get(pk=kwargs['pk'])
    ride.completed = True
    ride.save()
    message = "Thank you for completing this ride!!!"
    context = {"message": message}
    return render(request, "rideshare/mark_complete.html", context=context)


def confirmed_ride_driver_view(request, *args, **kwargs):
    confirmed_rides = list(OwnerRide.objects.filter(
        confirmed=True,
        completed=False,
        vehicle__driver=request.user
    ).order_by("arrivalTime"))

    context = {"confirmed_rides": confirmed_rides}
    return render(request, 'rideshare/confirmed_ride_driver.html', context=context)


def completed_ride_driver_view(request, *args, **kwargs):
    completed_rides = list(OwnerRide.objects.filter(
        confirmed=True,
        completed=True,
        vehicle__driver=request.user
    ).order_by("arrivalTime"))
    context = {"completed_rides": completed_rides}
    return render(request, 'rideshare/completed_ride.html', context=context)


def drive_confirm_view(request, *args, **kwargs):
    # mark the seleted ride as confirmed
    ride = OwnerRide.objects.get(pk=kwargs['pk'])
    ride.confirmed = True
    ride.vehicle = request.user.vehicle
    ride.save()

    # send email
    email_list = [ride.user.email]
    html_message="\
    <h2>Your ride request has been confirmed.</h2>\
    <h3>The ride info is:</h3>\
    <p>Ride Id: %s</br>\
    Destination Address: %s</br>\
    Arrival Time: %s</br>\
    Number of owner part passengers: %s</p>\
    <h3>\
    Enjoy your ride!!!</br>\
    Check for all the detail at our website.\
    </h3>\
    " % (ride.pk, ride.destaddr, ride.arrivalTime, ride.numPassengers)

    
    for sharer in ride.sharerride_set.all():
        email_list.append(sharer.user.email)
    send_mail(
        subject='Ride Confirmation -- Ride Sharing Service',   # subject
        message='email content',   # message
        from_email=settings.EMAIL_HOST_USER,   # from email
        recipient_list=email_list,
        fail_silently=False,
        html_message=html_message,        
    )

    message = "Confirm successfully!!!</br> You can go to \"My Rides\" tab to check everything"
    context = {"message": message}
    return render(request, 'rideshare/drive_confirm.html', context=context)


def make_a_drive_view(request, *args, **kwargs):
    if request.method == 'POST':
        arrival_start = request.POST.get('arrival_start')
        arrival_end = request.POST.get('arrival_end')

        arrival_start = datetime.strptime(arrival_start, "%Y-%m-%dT%H:%M")
        arrival_end = datetime.strptime(arrival_end, "%Y-%m-%dT%H:%M")
        arrival_start = arrival_start.astimezone(timezone.utc)
        arrival_end = arrival_end.astimezone(timezone.utc)
        rides = OwnerRide.objects.filter(
            confirmed=False,
            vehicleType=request.user.vehicle.vehicleType,
            arrivalTime__gte=arrival_start,
            arrivalTime__lte=arrival_end
        ).exclude(
            user=request.user,
        ).order_by("arrivalTime")
    else:
        rides = OwnerRide.objects.filter(
            confirmed=False,
            vehicleType=request.user.vehicle.vehicleType,
        ).exclude(
            user=request.user,
        ).order_by("arrivalTime")

    rides = [ride for ride in rides if ride.totalPassengerNum() + 1 <=\
             request.user.vehicle.capacity()]

    # remove rides whose sharers contain current user
    final_rides = []
    for ride in rides:
        sharers = ride.sharerride_set.filter(user=request.user)
        if sharers.count() == 0:
            final_rides.append(ride)

    message = "Found %s results which match your vehicle type." % (len(final_rides))
    vtinfo = VehicleTypeInfo().type_choices
    context = {'rides': final_rides, 'vtinfo': vtinfo,
               'message': message, }
    return render(request, 'rideshare/make_a_drive.html', context=context)


def all_rides_view(request, *args, **kwargs):
    context = {'user': request.user}
    return render(request, 'rideshare/all_rides.html', context = context)


def ride_join_view(request, *args, **kwargs):
    if request.method == 'POST':
        addr = request.POST.get('addr')
        arrival_start = request.POST.get('arrival_start')
        arrival_end = request.POST.get('arrival_end')
        num_seats = int(request.POST.get('num_seats'))

        arrival_start = datetime.strptime(arrival_start, "%Y-%m-%dT%H:%M")
        arrival_end = datetime.strptime(arrival_end, "%Y-%m-%dT%H:%M")
        arrival_start = arrival_start.astimezone(timezone.utc)
        arrival_end = arrival_end.astimezone(timezone.utc)                
        rides = OwnerRide.objects.filter(
            confirmed = False,
            shareable = True,
            destaddr__icontains = addr,
            arrivalTime__gte = arrival_start,
            arrivalTime__lte = arrival_end
        ).exclude(
            user=request.user,            
        ).order_by("arrivalTime")
        rides = [ride for ride in rides if \
                 num_seats + ride.totalPassengerNum() + 1 <=\
                 ride.vtinfo.max_capacity[ride.vehicleType]]

    else:
        rides = OwnerRide.objects.filter(
            confirmed = False,
            shareable = True,
            arrivalTime__gte = datetime.now(),
        ).exclude(
            user=request.user
        ).order_by("arrivalTime")[:10]
        rides = [ride for ride in rides if \
                 ride.totalPassengerNum() + 1 <\
                 ride.vtinfo.max_capacity[ride.vehicleType]]
        
    # remove rides whose sharers contain current user
    final_rides = []
    for ride in rides:
        sharers = ride.sharerride_set.filter(user=request.user)
        if sharers.count() == 0:
            final_rides.append(ride)
    if request.method == 'POST':
        message = "Found %s results." % (len(final_rides))
    else:
        message = "Overview of several closest rides from now."

    vtinfo = VehicleTypeInfo().type_choices
    capacity_list = VehicleTypeInfo().max_capacity
    context = {'rides': final_rides, 'vtinfo': vtinfo,
               'message': message, "capacity_list": capacity_list}
    return render(request, 'rideshare/ride_join.html', context=context)

def join_confirm_view(request, *args, **kwargs):
    # add to the sharer ride list
    if request.method == 'POST':
        pk = kwargs['pk']
        ride = OwnerRide.objects.get(pk=pk)
        num_passengers = int(request.POST.get('num_passengers'))
        # check if match the capacity
        if num_passengers + ride.totalPassengerNum() + 1 <= \
           ride.vtinfo.max_capacity[ride.vehicleType]:
            sharer = SharerRide(
                ownerride=ride,
                user=request.user,
                numPassengers=num_passengers
            )
            sharer.save()
            ride.sharerride_set.add(sharer)
            ride.save()
            messages.success(request, 'Join successfully.')
            return redirect('/ride_join')
        else:
            messages.error(
                request,
                "Join failed because the requested number of passengers is bigger than the available capacity of this ride."
            )
            return redirect('/ride_join')
    else:
        pk = kwargs['pk']
        ride = OwnerRide.objects.get(pk=pk)
        capacity_list = VehicleTypeInfo().max_capacity
        vtinfo = VehicleTypeInfo().type_choices
        context = {"ride": ride, "capacity_list": capacity_list,
                   "vtinfo": vtinfo}
        return render(request, 'rideshare/join_confirm.html', context=context)


def completed_ride_view(request, *args, **kwargs):
    completed_rides = list(OwnerRide.objects.filter(
        confirmed=True,
        completed=True,
        user=request.user
    ).order_by("arrivalTime"))
    sharer_completed_rides = SharerRide.objects.filter(
        user=request.user,
        ownerride__confirmed=True,
        ownerride__completed=True,
    )
    sharer_completed_rides = [ride.ownerride for ride in sharer_completed_rides]
    completed_rides += sharer_completed_rides
    context = {"completed_rides": completed_rides}
    return render(request, 'rideshare/completed_ride.html', context=context)


def confirmed_ride_view(request, *args, **kwargs):
    confirmed_rides = list(OwnerRide.objects.filter(
        confirmed=True,
        completed=False,
        user=request.user
    ).order_by("arrivalTime"))
    sharer_confirmed_rides = SharerRide.objects.filter(
        user=request.user,
        ownerride__confirmed=True,
        ownerride__completed=False,
    )
    sharer_confirmed_rides = [ride.ownerride for ride in sharer_confirmed_rides]
    confirmed_rides += sharer_confirmed_rides

    context = {"confirmed_rides": confirmed_rides}
    return render(request, 'rideshare/confirmed_ride.html', context=context)


def quit_joined_view(request, *args, **kwargs):
    # reset the info related to current ride
    ride = OwnerRide.objects.get(pk=kwargs['pk'])
    my_share = ride.sharerride_set.get(user=request.user)
    my_share.delete()
    ride.save()
    context = {}
    return render(request, "rideshare/quit_success.html", context=context)


def ride_detail_view(request, *args, **kwargs):
    ride = OwnerRide.objects.get(pk=kwargs['pk'])

    if ride.confirmed:
        driver = ride.vehicle.driver
    else:
        driver = None

    ride_owner = ride.user
    if ride.sharerride_set.count() != 0:
        ride_sharers = ride.sharerride_set.all()
    else:
        ride_sharers = None

    context = {'ride': ride, 'driver': driver,
               'ride_owner': ride_owner,
               'ride_sharers': ride_sharers,
               }
    return render(request, 'rideshare/ride_detail.html', context=context)


class edit_ride_view(SuccessMessageMixin, generic.UpdateView):
    model = OwnerRide
    form_class = RideRequestForm
    template_name = 'rideshare/edit_ride.html'
    success_url = "success/"
    success_message = "Changes successfully saved."
    

    def get_object(self):
        return self.model.objects.get(pk=self.kwargs['pk'])


def open_ride_view(request, *args, **kwargs):
    open_rides = list(OwnerRide.objects.filter(
        confirmed=False,
        completed=False,
        user=request.user
    ).order_by("arrivalTime"))
    joined_open_rides = SharerRide.objects.filter(
        user=request.user,
        ownerride__confirmed=False,
        ownerride__completed=False,
    )
    joined_open_rides = [ride.ownerride for ride in joined_open_rides]
    open_rides += joined_open_rides
    context = {"open_rides": open_rides}
    return render(request, 'rideshare/open_ride.html', context=context)

def ride_request_view(request, *args, **kwargs):
    if request.method == "POST":
        form = RideRequestForm(request.POST)

        if form.is_valid():
            ride = form.save(commit=False)
            ride.user = request.user
            ride.save()
            messages.success(request, 'Request successfully.')
            return redirect("/ride_request")
    else:
        form = RideRequestForm()

    context = {'form': form}
    return render(request, 'rideshare/ride_request.html', context = context)

def home_view(request, *args, **kwargs):
    introduction = "<h3>Want to request or join a ride?</h3>\
    <h3>Want to make a drive to help other people?</h3>\
    <h3>Here's the place! We can help you!</h3>"
    # user = User.objects.get(pk=request.user.pk)
    
    context = {
        'introduction': introduction,        
    }
    return render(request, 'rideshare/home.html', context=context)


def display_profile_view(request, *args, **kwargs):
    if request.method == "POST":        
        if "user_button" in request.POST:
            user_form = EditProfileForm(request.POST)
            request.user.first_name = user_form.data['first_name']
            request.user.last_name = user_form.data['last_name']
            request.user.email = user_form.data['email']

            # if modify the username
            if request.user.username != user_form.data['username']:
                if User.objects.filter(username=user_form.data['username']).\
                   exclude(pk=request.user.pk).count() == 0:
                    request.user.username = user_form.data['username']
                else:
                    messages.error(request, 'Change failed. The user name already exists')
                    return redirect('/edit_profile')
            request.user.save()
        elif "personal_button" in request.POST:
            personal_form = UserProfileForm(request.POST)
            print(personal_form.data['phoneNumber'])
            if personal_form.is_valid():
                if personal_form.data.get("phoneNumber"):                
                    request.user.userprofile.phoneNumber = personal_form.data['phoneNumber']
                if personal_form.data.get("birthday"):
                    request.user.userprofile.birthday = personal_form.data['birthday']
                if personal_form.data.get("gender"):
                    request.user.userprofile.gender = personal_form.data['gender']
                request.user.userprofile.save()
        elif "vehicle_button" in request.POST:
            vehicle_form = DriverProfileForm(request.POST)
            if vehicle_form.is_valid():
                request.user.vehicle.vehicleType = vehicle_form.data['vehicleType']
                request.user.vehicle.plateNum = vehicle_form.data['plateNum']
                request.user.vehicle.specialInfo = vehicle_form.data['specialInfo']
                request.user.vehicle.save()        
                # return redirect('/edit_profile')
        messages.success(request, 'Changes successfully saved.')
        return redirect('/edit_profile')
    else:
        if (hasattr(request.user, "vehicle")):
            vehicle_form = DriverProfileForm(instance = request.user.vehicle)
        else:
            vehicle_form = None
        user_form = EditProfileForm(instance = request.user)
        personal_form = UserProfileForm(instance = request.user.userprofile)
        success_message = None

    context = {'user_form': user_form,
               'vehicle_form': vehicle_form,
               'personal_form': personal_form,
               'success_message': success_message}
    return render(request, 'rideshare/edit_profile.html', context=context)


# edit the user profile
class edit_profile_view(SuccessMessageMixin, generic.UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'rideshare/edit_profile.html'
    success_url = '/edit_profile'
    success_message = "Edit Successfully"

    def get_object(self):
        return self.request.user


def driver_register_view(request, *args, **kwargs):    
    if request.method == "POST":
        form = DriverProfileForm(request.POST)        
        
        if form.is_valid():
            form = form.save(commit=False)
            form.driver = request.user
            form.save()
            return redirect("/")
    else:
        form = DriverProfileForm()

    context = {'form': form}
    return render(request, 'rideshare/driver_register.html', context=context)
