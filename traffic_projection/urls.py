"""
URL configuration for traffic_projection project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views as mv
from admins import views as admins
from users import views as usr

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # General
    path('', mv.index, name='index'),
    path('index/', mv.index, name='index'),
    path('UserLogin/', mv.userLogin, name='UserLogin'),
    path('Adminlogin/', mv.adminLogin, name='AdminLogin'),
    path('UserRegister/',mv.userRegistration, name='UserRegister'),


    path('base/', usr.base, name='base'),
    path('logout/', usr.logout_view, name='logout'),
    path('base/', usr.base, name='base'),
    path('logout/', usr.logout_view, name='logout'),
    path('UserLoginCheck/', usr.UserLoginCheck, name='UserLoginCheck'),
    path('UserRegisterForm/', usr.UserRegisterActions, name='UserRegisterForm'),
    path('UserHome/', usr.UserHome, name='UserHome'),
    path('projection/', usr.projection, name='projection'),
    path('training/', usr.training, name='training'),

    # path('viewdataset/', usr.viewdataset, name='viewdataset'), 


    path('AdminLogincheck/', admins.adminLoginCheck, name='AdminLoginCheck'),
    path('AdminHome/', admins.adminHome, name='AdminHome'),
    path('userDetails/', admins.RegisterUsersView, name='RegisterUsersView'),
    path('activateUser/<int:id>/', admins.activateUser, name='activate_users'),
    path('deactivateUser/<int:id>/', admins.deactivateUser, name='deactivate_users'),
    path('deleteUser/<int:id>/', admins.deleteUser, name='delete_users'),
    
]

# Static media support
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

