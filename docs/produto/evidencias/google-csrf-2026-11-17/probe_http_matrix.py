import urllib.request,urllib.error,urllib.parse,http.cookiejar,json,sys
from pathlib import Path
ORIGIN='https://hmgvaral.codehub.systems'
if '--allow-hmg'not in sys.argv:raise SystemExit('Use --allow-hmg to authorize anonymous HMG requests')
class StopRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
def probe(label,origin,referer):
 jar=http.cookiejar.CookieJar();op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),StopRedirect())
 with op.open(ORIGIN+'/api/auth/browser/v1/config',timeout=20)as r:
  cfg=json.load(r)
 token=next((c.value for c in jar if c.name=='csrftoken'),None)
 assert token,'Anonymous config did not provide CSRF cookie'
 body=urllib.parse.urlencode({'provider':'google','process':'login','callback_url':ORIGIN+'/entrar/retorno','csrfmiddlewaretoken':token}).encode()
 headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Varal-Google-CSRF-diagnostic'}
 if origin is not None:headers['Origin']=origin
 if referer is not None:headers['Referer']=referer
 request=urllib.request.Request(ORIGIN+'/api/auth/browser/v1/auth/provider/redirect',data=body,headers=headers)
 try:
  with op.open(request,timeout=20)as response:status=response.status;data=response.read().decode();location=response.headers.get('Location')
 except urllib.error.HTTPError as error:status=error.code;data=error.read().decode();location=error.headers.get('Location')
 result={'case':label,'status':status,'csrf_cookie_present':True,'csrf_form_matches_cookie':True,'origin_kind':'missing'if origin is None else 'null'if origin=='null'else'same-origin','referer_present':referer is not None,'csrf_failure_page':'CSRF'in data and status==403,'redirect_host':urllib.parse.urlsplit(location).hostname if location else None}
 if location and result['redirect_host']=='accounts.google.com':
  query=urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
  callback=query.get('redirect_uri',[''])[0]
  result['oauth_callback_origin']=urllib.parse.urlsplit(callback).scheme+'://'+(urllib.parse.urlsplit(callback).hostname or'')
  result['oauth_callback_path']=urllib.parse.urlsplit(callback).path
 return result
results=[probe('matching_form_origin_null_no_referer','null',None),probe('matching_form_same_origin_no_referer',ORIGIN,None),probe('matching_form_no_origin_no_referer',None,None),probe('matching_form_no_origin_valid_referer',None,ORIGIN+'/entrar')]

print(json.dumps(results,indent=2))
assert [r['status']for r in results]==[403,302,403,302], 'Observed CSRF/origin behavior differs from recorded HMG matrix'
