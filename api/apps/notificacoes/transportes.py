"""Bounded outbound transports; never log credentials or provider responses."""

import smtplib
import ssl
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests
import urllib3
from django.conf import settings
from django.core.mail import EmailMessage, get_connection

from .push import resolver_publico, validar_endpoint


@dataclass(frozen=True)
class Resultado:
    estado: str
    codigo: str = ""
    retry_after: str | None = None


class SessaoFixada:
    """requests-compatible post adapter. Resolver/CA/port injection is internal for TLS tests."""

    def __init__(self, *, resolver=resolver_publico, ssl_context=None, porta=443):
        self.resolver = resolver
        self.ssl_context = ssl_context
        self.porta = porta

    def post(self, endpoint, timeout=None, data=None, headers=None):
        host = validar_endpoint(endpoint)
        ip = self.resolver(host)
        url = urlsplit(endpoint)
        caminho = url.path or "/"
        if url.query:
            caminho += "?" + url.query
        headers = dict(headers or {})
        headers["Host"] = host
        pool = urllib3.HTTPSConnectionPool(
            ip,
            port=self.porta,
            server_hostname=host,
            assert_hostname=host,
            cert_reqs=ssl.CERT_REQUIRED,
            ssl_context=self.ssl_context,
            retries=False,
        )
        try:
            resposta = pool.urlopen(
                "POST",
                caminho,
                body=data,
                headers=headers,
                assert_same_host=False,
                redirect=False,
                retries=False,
                preload_content=False,
                timeout=urllib3.Timeout(connect=timeout, read=timeout),
            )
            try:
                # pywebpush eagerly accesses `.text`; never retain provider body.
                resultado = requests.Response()
                resultado.status_code = resposta.status
                resultado.reason = "provider response"
                resultado._content = b""
                if "Retry-After" in resposta.headers:
                    resultado.headers["Retry-After"] = resposta.headers["Retry-After"][:128]
                return resultado
            finally:
                resposta.close()
        finally:
            pool.close()


def enviar_push(inscricao, *, resolver=resolver_publico, ssl_context=None, porta=443):
    from pywebpush import WebPushException, webpush

    if (
        not settings.WEBPUSH_ENABLED
        or not settings.WEBPUSH_PRIVATE_KEY
        or not settings.WEBPUSH_SUBJECT
    ):
        return Resultado("descartada", "configuracao")
    try:
        host = validar_endpoint(inscricao["endpoint"])
        url = urlsplit(inscricao["endpoint"])
        inscricao = {
            **inscricao,
            "endpoint": "https://"
            + host
            + (url.path or "/")
            + ("?" + url.query if url.query else ""),
        }
        sessao = SessaoFixada(resolver=resolver, ssl_context=ssl_context, porta=porta)
        resposta = webpush(
            subscription_info=inscricao,
            data='{"titulo":"Novo aviso no Varal","destino":"/avisos"}',
            vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
            vapid_claims={"sub": settings.WEBPUSH_SUBJECT},
            ttl=60,
            timeout=settings.WEBPUSH_TIMEOUT_SECONDS,
            requests_session=sessao,
            verbose=False,
        )
        codigo = resposta.status_code
    except WebPushException as exc:
        resposta = exc.response
        if resposta is None:
            return Resultado("falhou", "push_invalido")
        codigo = resposta.status_code
    except (ValueError, ssl.SSLError):
        return Resultado("falhou", "destino_invalido")
    except Exception:
        # Network failures may follow an accepted POST. Never retry blindly.
        return Resultado("incerta", "rede_incerta")
    if 200 <= codigo < 300:
        return Resultado("aceita")
    if codigo in (404, 410):
        return Resultado("descartada", "inscricao_expirada")
    if codigo == 429:
        return Resultado("transiente", "provedor_temporario", resposta.headers.get("Retry-After"))
    if 500 <= codigo < 600:
        return Resultado("incerta", "provedor_incerto")
    return Resultado("falhou", "provedor_recusou")


def enviar_email(destinatario):
    conexao = get_connection(fail_silently=False, timeout=settings.EMAIL_TIMEOUT)
    try:
        conexao.open()
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPNotSupportedError, ssl.SSLError):
        return Resultado("falhou", "configuracao")
    except smtplib.SMTPConnectError as exc:
        return Resultado("transiente" if 400 <= exc.smtp_code < 500 else "falhou", "conexao")
    except smtplib.SMTPException:
        return Resultado("falhou", "configuracao")
    except OSError:
        return Resultado("transiente", "conexao")
    except Exception:
        return Resultado("falhou", "configuracao")
    try:
        mensagem = EmailMessage(
            "Novo aviso no Varal",
            f"Você tem um aviso no Varal. Acesse {settings.FRONTEND_URL.rstrip('/')}/avisos",
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            connection=conexao,
        )
        enviado = conexao.send_messages([mensagem])
        return Resultado("aceita") if enviado == 1 else Resultado("falhou", "nao_aceito")
    except (smtplib.SMTPDataError, smtplib.SMTPSenderRefused) as exc:
        return Resultado("transiente" if 400 <= exc.smtp_code < 500 else "falhou", "smtp_recusou")
    except smtplib.SMTPRecipientsRefused as exc:
        codigos = [v[0] for v in exc.recipients.values()]
        return Resultado(
            "transiente" if codigos and all(400 <= c < 500 for c in codigos) else "falhou",
            "smtp_recusou",
        )
    except Exception:
        return Resultado("incerta", "smtp_incerto")
    finally:
        try:
            conexao.close()
        except Exception:
            pass
