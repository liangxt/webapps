from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from mimetypes import guess_type

from tragether.models import *
from tragether.forms import *
import json


@login_required
def invite_unread_message(request):
    messages = ApplyInviteMsg.objects.filter(receiver=request.user, read_status=False, applied=False)
    return render(request, 'tragether/invite_unread_message.html', {'messages': messages})


@login_required
@transaction.atomic
def accept_invite_message(request, pk):
    message = get_object_or_404(ApplyInviteMsg, pk=pk)
    message.accept_status = True
    message.read_status = True
    message.save()
    user = Person.objects.get(user=request.user)
    user.travel_in.add(message.travel)
    return HttpResponseRedirect('/tragether/invite_unread_message')


@login_required
@transaction.atomic
def refuse_invite_message(request, pk):
    message = get_object_or_404(ApplyInviteMsg, pk=pk)
    message.accept_status = False
    message.read_status = True
    message.save()
    return HttpResponseRedirect('/tragether/invite_unread_message')


@login_required
def invite_history_message(request):
    messages = ApplyInviteMsg.objects.filter(receiver=request.user, read_status=True, applied=False)
    return render(request, 'tragether/invite_history_message.html', {'messages': messages})


@login_required
def invited_message(request):
    messages = ApplyInviteMsg.objects.filter(sender=request.user, applied=False)
    return render(request, 'tragether/invited_message.html', {'messages': messages})


@login_required
@transaction.atomic
def invite_travel(request, pk):
    if request.method == 'POST':
        travel = get_object_or_404(Travel, pk=pk)
        context = {}
        form = InvitationForm(request.POST)
        if form.is_valid():
            receiver = User.objects.get(id=request.POST['receiver'])
            # for user already in a travel group
            if travel.creator == receiver or Person.objects.filter(user=receiver, travel_in=travel).count() > 0:
                context['invite_message'] = 'Receiver already in this travel!'
                return HttpResponse(json.dumps(context), content_type='application/json')
            # for user just applied
            if ApplyInviteMsg.objects.filter(travel=travel, sender=receiver, receiver=travel.creator,
                                            applied=True, read_status=False).count() > 0:
                context['invite_message'] = "Receiver has applied to join this travel group."
                return HttpResponse(json.dumps(context), content_type='application/json')
            # for user just be invited
            if ApplyInviteMsg.objects.filter(travel=travel, sender=request.user, receiver=receiver,
                                            applied=False, read_status=False).count() > 0:
                context['invite_message'] = 'Receiver has been invited.'
                return HttpResponse(json.dumps(context), content_type='application/json')
            new_message = ApplyInviteMsg(travel=travel, sender=request.user,
                                         receiver=form.cleaned_data['receiver'], datetime=timezone.now(),
                                         subject=form.cleaned_data['subject'], content=form.cleaned_data['content'],
                                         applied=False)
            new_message.save()
            context['status'] = 'success'
            return HttpResponse(json.dumps(context), content_type='application/json')
        else:
            context['invite_error'] = form.errors
            return HttpResponse(json.dumps(context), content_type='application/json')
    else:
        raise Http404


@login_required
def get_unread_message(request):
    number = ApplyInviteMsg.objects.filter(receiver=request.user, read_status=False).count()
    context = {'number': number}
    return HttpResponse(json.dumps(context), content_type='application/json')


@login_required
def vote_attraction(request):
    if request.method == 'POST':
        travel = Travel.objects.get(id=request.POST['id'])
        poll = Poll.objects.get(travel=travel)
        context = {}
        number = []
        attractions = []
        for tmp in poll.attraction.all():
            if tmp.id == int(request.POST['new_vote']):
                if tmp.votes.exists(request.user.id):
                    context['status'] = '0'
                else:
                    tmp.votes.up(request.user.id)
                    context['status'] = '1'
                break
        total = 0
        for tmp in poll.attraction.all():
            total += int(tmp.votes.count())
        for tmp in poll.attraction.all():
            number.append(int(int(tmp.votes.count()) * 100 / total))
            attractions.append(tmp.name)
        context['number'] = number
        context['attractions'] = attractions
        return HttpResponse(json.dumps(context), content_type='application/json')
    else:
        raise Http404
        

@login_required
def apply_unread_message(request):
    messages = ApplyInviteMsg.objects.filter(receiver=request.user, read_status=False, applied=True)
    return render(request, 'tragether/apply_unread_message.html', {'messages': messages})


@login_required
@transaction.atomic
def accept_apply_message(request, user, pk):
    message = get_object_or_404(ApplyInviteMsg, pk=pk)
    message.accept_status = True
    message.read_status = True
    message.save()
    user = Person.objects.get(user=User.objects.get(username=user))
    user.travel_in.add(message.travel)
    return HttpResponseRedirect('/tragether/apply_unread_message')


@login_required
@transaction.atomic
def refuse_apply_message(request, pk):
    message = get_object_or_404(ApplyInviteMsg, pk=pk)
    message.accept_status = False
    message.read_status = True
    message.save()
    return HttpResponseRedirect('/tragether/apply_unread_message')


@login_required
def apply_history_message(request):
    messages = ApplyInviteMsg.objects.filter(receiver=request.user, read_status=True, applied=True)
    return render(request, 'tragether/apply_history_message.html', {'messages': messages})


@login_required
def applied_message(request):
    messages = ApplyInviteMsg.objects.filter(sender=request.user, applied=True)
    return render(request, 'tragether/applied_message.html', {'messages': messages})


@login_required
@transaction.atomic
def apply_travel(request, pk):
    travel = get_object_or_404(Travel, pk=pk)
    # for user already in a travel group
    if travel.creator == request.user or Person.objects.filter(user=request.user, travel_in=travel):
        return redirect(reverse('travel_group', kwargs={'pk':pk}))
    # for user just applied
    if ApplyInviteMsg.objects.filter(travel=travel, sender=request.user, receiver=travel.creator,
                                    applied=True, read_status=False).count() > 0:
        message = "You have applied to join this travel group. Please wait for the response from the creator."
        return render(request, 'tragether/404.html', {'message':message})
    # for user just be invited
    if ApplyInviteMsg.objects.filter(travel=travel, sender=travel.creator, receiver=request.user,
                                    applied=False, read_status=False).count() > 0:
        message = "You have been invited to join this travel group. Please check your invitation messages."
        return render(request, 'tragether/404.html', {'message':message})
    # for closed travel
    if travel.status == '0':
        message = "Sorry, this travel group is closed. Please find other groups to join or create your own travel!"
        return render(request, 'tragether/404.html', {'message':message})
    # for who can apply
    if request.method == 'GET':
        return render(request, 'tragether/apply_travel.html', {'form': ApplicationForm})
    form = ApplicationForm(request.POST)
    if form.is_valid():
        new_message = ApplyInviteMsg(travel=travel, sender=request.user,
                                     receiver=travel.creator, datetime=timezone.now(),
                                     subject=form.cleaned_data['subject'], content=form.cleaned_data['content'],
                                     applied=True)
        new_message.save()
    else:
        return render(request, 'tragether/apply_travel.html', {'form': form})
    return HttpResponseRedirect('/')


@login_required
@transaction.atomic
def create_new_travel(request):
    if request.method == 'GET':
        return render(request, 'tragether/create_new_travel.html', {'form': CreateTravelForm})
    form = CreateTravelForm(request.POST)
    if form.is_valid():
        new_travel = Travel(creator=request.user,
                            destination=form.cleaned_data['destination'],
                            group_size=form.cleaned_data['group_size'],
                            start_time=form.cleaned_data['start_time'],
                            end_time=form.cleaned_data['end_time'],
                            budget=form.cleaned_data['budget'],
                            info=form.cleaned_data['info'],
                            status=form.cleaned_data['status'])
        new_travel.save()
        new_poll = Poll(travel=new_travel)
        new_poll.save()
        return HttpResponseRedirect(reverse('travel_group', kwargs={'pk': new_travel.pk}))
    else:
        return render(request, 'tragether/create_new_travel.html', {'form': form})


@login_required
@transaction.atomic
def travel_group(request, pk):
    travel = get_object_or_404(Travel, pk=pk)
    if travel.creator.username != request.user.username\
            and Person.objects.filter(user=request.user, travel_in=travel).count() == 0:
        return render(request, 'tragether/no_group_permission.html', {'id': pk})
    context = {}
    context['travel'] = travel
    context['form_travel_edit'] = CreateTravelForm(instance=travel)
    context['form_chatbox_messages'] = ChatboxForm()
    context['form_itinerary'] = ItineraryForm()
    context['form_invite'] = InvitationForm()
    context['group_memebers'] = Person.objects.all().filter(travel_in=travel)
    context['creator'] = Person.objects.get(user=travel.creator)

    poll = Poll.objects.get(travel=travel)
    context['add_form'] = AddAttractionForm()
    attractions = []
    flag = True
    if request.method == 'GET':
        context['poll_form'] = PollForm(poll)
    else:
        add_form = AddAttractionForm(request.POST)
        if not add_form.is_valid():
            flag = False
            context['error_message'] = add_form['name'].errors
        else:
            for tmp in poll.attraction.all():
                if tmp.name == add_form.cleaned_data['name']:
                    flag = False
                    context['error_message'] = "Attraction already exist!"
                    break
        if flag:
            new_attraction = Attraction(name=add_form.cleaned_data['name'])
            new_attraction.save()
            poll.attraction.add(new_attraction)
            
    context['poll_form'] = PollForm(poll)
    total = 0
    for tmp in poll.attraction.all():
        total += int(tmp.votes.count())
    for tmp in poll.attraction.all():
        place = {}
        place['name'] = tmp.name
        if total != 0:
            place['number'] = int(int(tmp.votes.count()) * 100 / total)
        else:
            place['number'] = 0
        attractions.append(place)
    context['attractions'] = attractions
    return render(request, 'tragether/travel_group.html', context)
    

@login_required
def my_travel(request):
    create_travels = Travel.objects.filter(creator=request.user).order_by('-id')
    profile = Person.objects.get(user=request.user)
    in_travels = profile.travel_in.all().order_by('-id')
    return render(request, 'tragether/my_travel.html', {'travels': create_travels, 'in_travels': in_travels,
                                                        'profile': profile, 'form1': EditUserInforForm(instance=request.user),
                                                        'form2': EditProfileForm(instance=profile)})


@login_required
def users_profile(request, user):
    u = get_object_or_404(User, username=user)
    profile = Person.objects.get(user=u)
    create_travels = Travel.objects.filter(creator=u).order_by('-id')
    in_travels = profile.travel_in.all().order_by('-id')
    return render(request, 'tragether/users_profile.html', {'user_profile': profile, 'travels': create_travels,
                                                            'in_travels': in_travels})


@login_required
@transaction.atomic
def edit_profile(request):
    profile = Person.objects.get(user=request.user)
    context = {}
    context['profile'] = profile
    if request.method == 'GET':
        context['form1'] = EditUserInforForm(instance=request.user)
        context['form2'] = EditProfileForm(instance=profile)
        return render(request, 'tragether/edit_profile.html', context)
    user_form = EditUserInforForm(request.POST, instance=request.user)
    profile_form = EditProfileForm(request.POST, request.FILES, instance=Person(user=request.user))
    if user_form.is_valid() and profile_form.is_valid():
        profile = Person.objects.get(user=request.user)
        profile.age = profile_form.cleaned_data['age']
        profile.bio = profile_form.cleaned_data['bio']
        profile.picture = profile_form.cleaned_data['picture']
        profile.user.last_name = user_form.cleaned_data['last_name']
        profile.user.first_name = user_form.cleaned_data['first_name']
        profile.user.set_password(user_form.cleaned_data['password'])
        profile.user.save()
        profile.save()
        login(request, profile.user)
        return HttpResponseRedirect('/tragether/my_travel')
    else:
        context['form1'] = user_form
        context['form2'] = profile_form
        return render(request, 'tragether/edit_profile.html', context)


@login_required
@transaction.atomic
def edit_travel(request, travel_id):
    travel = get_object_or_404(Travel, id=travel_id)
    if request.method == 'POST':
        form_travel_edit = CreateTravelForm(request.POST, instance=travel)
        if not form_travel_edit.is_valid():
            return HttpResponse(json.dumps(form_travel_edit.errors), content_type="application/json")
        else:
            form_travel_edit.save()
            return HttpResponse(json.dumps({"content":"valid"}), content_type="application/json")
    else:
        raise Http404


@login_required
def home(request):
    context = {}
    if request.method == 'GET':
        context['travel_groups'] = Travel.objects.all().order_by('-status', 'start_time')
        context['form_search_group'] = SearchGroupForm()
        return render(request, 'tragether/home.html', context)
    form_search_group = SearchGroupForm(request.POST)
    context['form_search_group'] = form_search_group
    if not form_search_group.is_valid():
        context['travel_groups'] = Travel.objects.all().order_by('-status', 'start_time')
        return render(request, 'tragether/home.html', context)
    des = form_search_group.cleaned_data['destination']
    start_time = form_search_group.cleaned_data['start_time']
    end_time = form_search_group.cleaned_data['end_time']
    group_obj = Travel.objects.filter(destination__icontains=des).order_by('-status', 'start_time')
    if start_time:
        group_obj = group_obj.filter(start_time__gte=start_time)
    if end_time:
        group_obj = group_obj.filter(end_time__lte=end_time)
    context['travel_groups'] = group_obj
    return render(request, 'tragether/home.html', context)


@login_required
@transaction.atomic
def add_chatbox_msg(request, travel_id):
    travel = get_object_or_404(Travel, id=travel_id)
    if request.method == 'POST':
        form = ChatboxForm(request.POST)
        if not form.is_valid():
            return HttpResponse(json.dumps(form.errors), content_type="application/json")
        else:
            new_chat_msg = Chatbox_Messages(travel=travel,
                sender=request.user,
                content=request.POST['content'],
                datetime=timezone.now())
            new_chat_msg.save()  
            return HttpResponse(json.dumps({"content":"valid", "new_chat_msg_html":new_chat_msg.html}), content_type="application/json")
    else:
        raise Http404


@login_required
def get_chatbox_msg(request, travel_id):
    travel = get_object_or_404(Travel, id=travel_id)
    chat_msgs = Chatbox_Messages.objects.filter(travel=travel).order_by('datetime')
    context = {"chat_msgs":chat_msgs,}
    return render(request, 'tragether/chat_msgs.json', context, content_type='application/json')


@login_required
@transaction.atomic
def add_itinerary(request, travel_id):
    travel = get_object_or_404(Travel, id=travel_id)
    if request.method == 'POST':
        form_itinerary = ItineraryForm(request.POST)
        if not form_itinerary.is_valid():
            return HttpResponse(json.dumps(form_itinerary.errors), content_type="application/json")
        else:
            new_itinerary = Itinerary(travel=travel,
                place=form_itinerary.cleaned_data['place'],
                start_time=form_itinerary.cleaned_data['start_time'],
                latitude=request.POST['latitude'],
                longitude=request.POST['longitude'])
            new_itinerary.save()
            return HttpResponse(json.dumps({"content":"valid"}), content_type="application/json")
    else:
        raise Http404


@login_required
@transaction.atomic
def delete_itinerary(request, itinerary_id):
    itinerary_to_delete = get_object_or_404(Itinerary, id=itinerary_id)
    itinerary_to_delete.deleted = True
    itinerary_to_delete.save()
    return HttpResponse("")


@login_required
@transaction.atomic
def edit_itinerary(request, itinerary_id):
    itinerary_to_edit = get_object_or_404(Itinerary, id=itinerary_id)
    if request.method == 'POST':
        form_itinerary = ItineraryForm(request.POST, instance=itinerary_to_edit)
        if not form_itinerary.is_valid():
            return HttpResponse(json.dumps(form_itinerary.errors), content_type="application/json")
        else:
            form_itinerary.save()
            if request.POST['latitude'] != 'None' or request.POST['longitude'] != 'None':
                itinerary_to_edit.latitude = request.POST['latitude']
                itinerary_to_edit.longitude = request.POST['longitude']
                itinerary_to_edit.save()
            return HttpResponse(json.dumps({"content":"valid"}), content_type="application/json")
    else:
        raise Http404


@login_required
def get_itinerary(request, travel_id):
    travel = get_object_or_404(Travel, id=travel_id)
    max_time = Itinerary.get_max_time(travel)
    itineraries = Itinerary.get_itineraries(travel)
    context = {"itineraries":itineraries, "max_time":max_time}
    return render(request, 'tragether/itineraries.json', context, content_type='application/json')


@login_required
def update_itinerary(request, travel_id, time="1970-01-01T00:00+00:00"):
    travel = get_object_or_404(Travel, id=travel_id)
    try: 
        itineraries = Itinerary.update_itineraries(travel, time)
    except:
        raise Http404
    max_time = Itinerary.get_max_time(travel)
    context = {"itineraries":itineraries, "max_time":max_time}
    return render(request, 'tragether/itineraries.json', context, content_type='application/json')


### Not require log in below ###

@transaction.atomic
def register(request):
    if request.method == 'GET':
        return redirect('/tragether/welcome')
    context = {}
    context['form'] = AuthenticationForm()
    context['form_reset'] = EmailForm()
    form_register = RegistrationForm(request.POST)
    if not form_register.is_valid():
        context['form_register'] = form_register
        return render(request, 'tragether/welcome.html', context)
    new_user = User.objects.create_user(username=form_register.cleaned_data['username'],
                                        first_name=form_register.cleaned_data['first_name'],
                                        last_name=form_register.cleaned_data['last_name'],
                                        email=form_register.cleaned_data['email'],
                                        password=form_register.cleaned_data['password1'])
    new_user.is_active = False
    new_user.save()
    new_person = Person(user=new_user,
                        gender=form_register.cleaned_data['gender'])
                        #age=form_register.cleaned_data['age'],
                        #bio=form_register.cleaned_data['bio'])
    new_person.save()
    token = default_token_generator.make_token(new_user)
    email_body = """
Welcome to Tragether! Please click the link below to verify your email address
and complete the registration of your account:

  http://%s%s
""" % (request.get_host(), 
       reverse('register_confirm', args=(new_user.username, token)))
    send_mail(subject="Verify your email address",
              message=email_body,
              from_email="webappdev2016@gmail.com",
              recipient_list=[new_user.email])
    context['email'] = form_register.cleaned_data['email']
    context['extra_message'] = 'register-success'
    context['form_register'] = RegistrationForm()
    return render(request, 'tragether/welcome.html', context) 


@transaction.atomic
def register_confirm(request, username, token):
    logout(request)
    user = get_object_or_404(User, username=username)
    if not default_token_generator.check_token(user, token):
        raise Http404
    user.is_active = True
    user.save()
    context = {}
    context['extra_message'] = 'register-confirmed'
    context['form'] = AuthenticationForm()
    context['form_register'] = RegistrationForm()
    context['form_reset'] = EmailForm()
    return render(request, 'tragether/welcome.html', context)


@transaction.atomic
def reset_password(request):
    if request.method == 'GET':
        return redirect('/tragether/welcome')
    context = {}
    context['form'] = AuthenticationForm()
    context['form_register'] = RegistrationForm()
    form_reset = EmailForm(request.POST)
    if not form_reset.is_valid():
        context['form_reset'] = form_reset
        return render(request, 'tragether/welcome.html', context)
    user = get_object_or_404(User, email=form_reset.cleaned_data['email'])
    token = default_token_generator.make_token(user)
    email_body = """
Please click the link below to reset your password:

  http://%s%s
""" % (request.get_host(),
       reverse('reset_password_confirm', args=(user.username, token)))
    send_mail(subject="Reset your password",
              message=email_body,
              from_email="webappdev2016@gmail.com",
              recipient_list=[user.email])
    context['email'] = form_reset.cleaned_data['email']
    context['extra_message'] = 'reset-password-success'
    context['form_reset'] = EmailForm()
    return render(request, 'tragether/welcome.html', context) 


@transaction.atomic
def reset_password_confirm(request, username, token):
    logout(request)
    context = {}
    context['username'] = username
    context['token'] = token
    user = get_object_or_404(User, username=username)
    if not default_token_generator.check_token(user, token):
        raise Http404
    context['form'] = AuthenticationForm()
    context['form_register'] = RegistrationForm()
    context['form_reset'] = EmailForm()
    if request.method == 'GET':
        context['extra_message'] = 'reset-password-pswd'
        context['form_reset_password'] = PSWDForm()
        return render(request, 'tragether/welcome.html', context)
    form_reset_password = PSWDForm(request.POST)
    if not form_reset_password.is_valid():
        context['extra_message'] = 'reset-password-pswd'
        context['form_reset_password'] = form_reset_password
        return render(request, 'tragether/welcome.html', context)
    user.set_password(form_reset_password.cleaned_data['password1'])
    user.save()
    context['extra_message'] = 'reset-password-confirmed'
    return render(request, 'tragether/welcome.html', context)


def handler_404(request):
    message = "Oops, nothing here."
    return render(request, 'tragether/404.html', {'message':message})
