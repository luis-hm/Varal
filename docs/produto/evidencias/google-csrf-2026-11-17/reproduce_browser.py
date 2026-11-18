"""Anonymous real-browser Google-start probe. Persists only sanitized booleans/paths."""
import argparse,json,subprocess,uuid,urllib.parse,os,time,shutil,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--policy',choices=['strict-origin','same-origin']);p.add_argument('--assert-google-start',action='store_true');p.add_argument('--allow-hmg',action='store_true');args=p.parse_args()
if not args.allow_hmg:p.error('Use --allow-hmg to authorize anonymous OAuth-start requests to the HMG environment')
os.umask(0o077);out=Path(tempfile.mkdtemp(prefix='varal-google-csrf-'));session='google-csrf-probe-'+uuid.uuid4().hex[:10]
cli=shutil.which('agent-browser');js=os.environ.get('AGENT_BROWSER_JS')
if cli:b=[cli,'--session',session,'--json']
elif js and Path(js).is_file():b=['node',js,'--session',session,'--json']
else:raise SystemExit('Install agent-browser first or set AGENT_BROWSER_JS to its existing local JS entrypoint')
def cmd(*arguments,js=None):
 r=subprocess.run(b+list(arguments),input=js,text=True,capture_output=True,timeout=40)
 try: data=json.loads(r.stdout)
 except ValueError: raise RuntimeError('Browser CLI failed; raw output suppressed')from None
 if not data.get('success'):raise RuntimeError('Browser action failed; raw error suppressed')
 return data.get('data')
def ev(js):
 d=cmd('eval','--stdin',js=js)
 # CLI eval's envelope may contain a full URL; discard it immediately.
 return d.get('result',d)if isinstance(d,dict)else d
report={'environment':'HMG','policy_override_local':args.policy,'anonymous_session':True,'account_authenticated':False}
try:
 cmd('open','https://hmgvaral.codehub.systems/entrar')
 cmd('wait','--fn',"!!document.querySelector('form[action*=\"provider/redirect\"]') && ![...document.querySelectorAll('button')].find(x=>x.innerText.includes('Continuar com Google'))?.disabled")
 policy=json.dumps(args.policy)
 report['before']=ev('''(() => { const f=document.querySelector('form[action*="provider/redirect"]'); const cookie=()=>document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.slice(10)||''; f.addEventListener('formdata',e=>{const ts=e.formData.getAll('csrfmiddlewaretoken');sessionStorage.setItem('qaProbe',JSON.stringify({csrfEqualsCookie:ts.length===1&&ts[0]===cookie(),cookiePresent:!!cookie(),csrfFieldCount:ts.length,csrfFieldPresent:ts.some(Boolean)}))}); const policy='''+policy+'''; if(policy){const m=document.createElement('meta');m.name='referrer';m.content=policy;document.head.append(m)} return {origin:location.origin,path:location.pathname,cookiePresent:!!cookie(),hiddenTokenCount:f.querySelectorAll('[name=csrfmiddlewaretoken]').length}; })()''')
 cmd('find','role','button','click','--name','Continuar com Google')
 for attempt in range(25):
  try:
   page=ev("({origin:location.origin,path:location.pathname,title:document.title,csrfError:document.body.innerText.includes('CSRF')&&document.body.innerText.includes('403'),googleError:document.body.innerText.includes('redirect_uri_mismatch')?'redirect_uri_mismatch':null,formdata:location.hostname==='hmgvaral.codehub.systems'?JSON.parse(sessionStorage.getItem('qaProbe')||'null'):null})")
   if isinstance(page,dict)and(page.get('csrfError')or page.get('origin')=='https://accounts.google.com'):break
  except RuntimeError:pass
  time.sleep(.1)
 else:raise RuntimeError('Expected provider navigation did not settle')
 report['page']={key:page.get(key)for key in ['origin','path','title','csrfError','googleError','formdata']}
 rows=cmd('network','requests')['requests'];posts=[r for r in rows if r.get('method')=='POST'and urllib.parse.urlsplit(r['url']).path=='/api/auth/browser/v1/auth/provider/redirect'];post=posts[-1];headers={k.lower():v for k,v in post.get('headers',{}).items()};fields=urllib.parse.parse_qs(post.get('postData',''),keep_blank_values=True)
 report['request']={'method':'POST','path':'/api/auth/browser/v1/auth/provider/redirect','status':post.get('status'),'origin_header':headers.get('origin'),'referer_present':'referer'in headers,'csrf_post_present':bool(fields.get('csrfmiddlewaretoken',[''])[0]),'csrf_post_count':len(fields.get('csrfmiddlewaretoken',[]))}
 report['app_google_start_passed']=not page['csrfError']and page['origin']=='https://accounts.google.com'
 report['full_google_login_validated']=False
 label='counter'if args.policy else'baseline'
 (out/('probe-'+label+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 if args.assert_google_start and not report['app_google_start_passed']:raise SystemExit(1)
finally:
 subprocess.run(b+['close'],capture_output=True,text=True)
