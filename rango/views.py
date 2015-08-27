from django.shortcuts import render, redirect
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random
import string
from datetime import datetime
from rango.bing_search import run_query 

# Create your views here.

#def index(request):
	#request.session.set_test_cookie()
#	category_list = Category.objects.order_by('-likes')[:5]
#	page_list = Page.objects.order_by('-views')[:5]
#	context_dict = {'categories': category_list, 'pages': page_list}
#	return render(request, 'rango/index.html', context_dict)

def index(request):
	category_list = Category.objects.order_by('-likes')[:5]
	page_list = Page.objects.order_by('-views')[:5]
	context_dict = {'categories':category_list, 'pages': page_list}

	visits = request.session.get('visits')
	if not visits:
		visits = 1

	reset_last_visit_time = False

	last_visit = request.session.get('last_visit')
	if last_visit:
		last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")	
		if (datetime.now() - last_visit_time).seconds > 0:
			visits = visits+1
			reset_last_visit_time = True
	else:
		reset_last_visit_time = True

	if reset_last_visit_time:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = visits

	context_dict['visits'] = visits
	response = render(request,'rango/index.html',context_dict)
	return response

def about(request):
	visits = request.session.get('visits')
	if not visits:
		visits = 1
	context_dict = {'visits': visits}
	return render(request, 'rango/about.html', context_dict)

def category(request, category_name_slug):
	context_dict = {}

	try:
		category = Category.objects.get(slug=category_name_slug)
		context_dict['category_name'] = category.name

		pages = Page.objects.filter(category=category).order_by('-views')

		context_dict['pages'] = pages

		context_dict['category'] = category
		context_dict['category_name_slug'] = category_name_slug

	except Category.DoesNotExist:
		pass

	query, result_list = search(request)
	if len(result_list) != 0:
		context_dict['result_list'] = result_list
	if query != None:
		context_dict['query'] = query 

	return render(request, 'rango/category.html', context_dict)

def add_category(request):
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			form.save(commit=True)
			return index(request)
		else:
			print form.errors
	else:
		form = CategoryForm()
	return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):

	try:
		cat = Category.objects.get(slug=category_name_slug)
	except Category.DoesNotExist:
		cat = None

	if request.method == 'POST':
		form = PageForm(request.POST)
		if form.is_valid():
			if cat:
				page = form.save(commit=False)
				page.category = cat
				page.views = 0
				page.save()
				return category(request, category_name_slug)
		else:
			print form.errors
	else:
		form = PageForm()
	context_dict = {'form':form, 'category':cat}

	return render(request, 'rango/add_page.html', context_dict)

def register(request):
	registered = False
	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			profile.save()

			registered = True

		else:
			print user_form.errors, profile_form.errors

	else:
		user_form = UserForm()
		profile_form = UserProfileForm()

	return render(request,'rango/register.html',
					{'user_form':user_form, 'profile_form':profile_form,
					 'registered':registered})

def user_login(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')

		user = authenticate(username=username, password=password)

		if user:
			if user.is_active:
				login(request,user)
				return HttpResponseRedirect('/rango/')
			else:
				return HttpResponse("Your Rango account is disabled.")
		else:
			print "Invalid login details: {0}, {1}".format(username,password)
			return render(request, 'rango/login.html', {"login_failed": "true"})
			#return HttpResponse("Invalid login details supplied. <br/><a href='/rango/login/'>Retry</a><br/><a href='/rango/forgot/'>Forgot password?</a>")
	else:
		return render(request,'rango/login.html', {})

@login_required
def restricted(request):
	return HttpResponse("Since you're logged in, you can see this text! <br/><a href='/rango/'> To go back to the home page, click here </a>")

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/rango/')

def generate_pass():
	choice = string.ascii_uppercase+string.ascii_lowercase+string.digits
	chars = [random.choice(choice) for _ in range(20)]
	return ''.join(chars)

def forgot(request):
	context_dict = {}
	if request.method == 'POST':
		username = request.POST.get('username')
		email = request.POST.get('email')
		users = User.objects.all()
		for user in users:
			if str(user) == str(username):
				if str(user.email) == str(email):
					temp = generate_pass()
					send_mail('Password reset', 'A temporary password has been assigned to you: '+temp, 'samlunj@gmail.com', [str(email)], fail_silently=False)
					context_dict['authenticate'] = 'True'
					user.set_password(temp)
					user.save()

	return render(request, 'rango/forgot.html', context_dict)

def reset(request):
	print "hello"
	context_dict = {}
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		new_pw = request.POST.get('new_password')
		user = authenticate(username=username, password=password)

		if user:
			user.set_password(new_pw)
			user.save()
			context_dict['reset'] = 'True'

	return render(request, 'rango/password_reset.html', context_dict)

def search(request):
	result_list = []
	query = None
	if request.method == 'POST':
		query = request.POST['query'].strip()

		if query:
			result_list = run_query(query)

	return query, result_list

def track_url(request):
	page_id = None
	url = '/rango/'
	if request.method == 'GET':
		if 'page_id' in request.GET:
			page_id = request.GET['page_id']
			try:
				page = Page.objects.get(id=page_id)
				page.views = page.views + 1
				page.save()
				url = page.url
			except:
				pass
	return redirect(url)

@login_required
def like_category(request):
	cat_id = None
	if request.method == 'GET':
		cat_id = request.GET['category_id']
	likes = 0
	if cat_id:
		cat = Category.objects.get(id=int(cat_id))
		if cat:
			likes = cat.likes + 1
			cat.likes = likes
			cat.save()
	return HttpResponse(likes)

def get_category_list(max_results=0, starts_with=''):
	cat_list = []
	if starts_with:
		cat_list = Category.objects.filter(name__istartswith=starts_with)
	if max_results > 0:
		if (len(cat_list) > max_results):
			cat_list = cat_list[:max_results]
	return cat_list

def suggest_category(request):
	cat_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
	cat_list = get_category_list(8, starts_with)
	return render(request,'rango/category_list.html', {'cat_list': cat_list})
