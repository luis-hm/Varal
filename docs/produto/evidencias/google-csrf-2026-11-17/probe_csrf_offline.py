"""Offline CSRF boundary probe: synthetic values only, no DB or network."""
import json
from django.conf import settings
settings.configure(SECRET_KEY='synthetic-not-used-in-varal', DEBUG=False, ALLOWED_HOSTS=['hmgvaral.codehub.systems'], CSRF_TRUSTED_ORIGINS=['https://hmgvaral.codehub.systems'], USE_I18N=False, DEFAULT_CHARSET='utf-8')
from django.test import RequestFactory
from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware

class Probe(CsrfViewMiddleware):
 def _reject(self,request,reason):
  request.rejection=reason
  return HttpResponse(status=403)

rf=RequestFactory();secret='a'*32;other='b'*32;domain='hmgvaral.codehub.systems';origin='https://'+domain
cases=[
 ('origin_valid_cookie_body_match',{'HTTP_ORIGIN':origin},secret,secret,None,200),
 ('origin_null_cookie_body_match',{'HTTP_ORIGIN':'null'},secret,secret,None,403),
 ('origin_absent_referer_absent_https',{},secret,secret,None,403),
 ('origin_absent_referer_same_origin',{'HTTP_REFERER':origin+'/entrar'},secret,secret,None,200),
 ('origin_foreign_cookie_body_match',{'HTTP_ORIGIN':'https://invalid.example'},secret,secret,None,403),
 ('cookie_rotated_old_body',{'HTTP_ORIGIN':origin},other,secret,None,403),
 ('cookie_missing_valid_body',{'HTTP_ORIGIN':origin},None,secret,None,403),
 ('empty_body_valid_header',{'HTTP_ORIGIN':origin},secret,'',secret,200),
 ('wrong_nonempty_body_valid_header',{'HTTP_ORIGIN':origin},secret,other,secret,403),
]
results=[]
for name,headers,cookie,body,header,expected in cases:
 if header:headers['HTTP_X_CSRFTOKEN']=header
 request=rf.post('/api/auth/browser/v1/auth/provider/redirect',{'provider':'google','process':'login','callback_url':origin+'/entrar/retorno','csrfmiddlewaretoken':body},secure=True,HTTP_HOST=domain,**headers)
 if cookie:request.COOKIES['csrftoken']=cookie
 middleware=Probe(lambda request:HttpResponse(status=200));middleware.process_request(request)
 result=middleware.process_view(request,lambda request:HttpResponse(status=200),(),{})
 status=200 if result is None else result.status_code
 assert status==expected,(name,status)
 results.append({'case':name,'status':status,'expected':expected,'rejection_category':getattr(request,'rejection',None)})
print(json.dumps({'passed':True,'cases':results},indent=2))
