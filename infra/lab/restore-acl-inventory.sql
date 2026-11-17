-- Compare only opaque hashes in private files. Run after Collector and before cutover.
-- Exact equality is conservative: any changed auth/ACL state blocks reopening.
SET TIME ZONE 'UTC';
COPY (
    SELECT 'usuario' AS kind, id::text AS identity,
           encode(sha256(convert_to(json_build_array(id,email,password,is_active,is_staff,is_superuser,prefs_notificacao)::text,'UTF8')),'hex') AS state
      FROM contas_usuario_usuario
    UNION ALL
    SELECT 'usuario_grupo', id::text,
           encode(sha256(convert_to(json_build_array(id,usuario_id,group_id)::text,'UTF8')),'hex')
      FROM contas_usuario_usuario_groups
    UNION ALL
    SELECT 'usuario_permissao', id::text,
           encode(sha256(convert_to(json_build_array(id,usuario_id,permission_id)::text,'UTF8')),'hex')
      FROM contas_usuario_usuario_user_permissions
    UNION ALL
    SELECT 'grupo_auth', id::text,
           encode(sha256(convert_to(json_build_array(id,name)::text,'UTF8')),'hex')
      FROM auth_group
    UNION ALL
    SELECT 'grupo_permissao', id::text,
           encode(sha256(convert_to(json_build_array(id,group_id,permission_id)::text,'UTF8')),'hex')
      FROM auth_group_permissions
    UNION ALL
    SELECT 'permissao', id::text,
           encode(sha256(convert_to(json_build_array(id,content_type_id,codename)::text,'UTF8')),'hex')
      FROM auth_permission
    UNION ALL
    SELECT 'email', id::text,
           encode(sha256(convert_to(json_build_array(id,user_id,email,verified,"primary")::text,'UTF8')),'hex')
      FROM account_emailaddress
    UNION ALL
    SELECT 'social', id::text,
           encode(sha256(convert_to(json_build_array(id,user_id,provider,uid)::text,'UTF8')),'hex')
      FROM socialaccount_socialaccount
    UNION ALL
    SELECT 'ticket_google', id::text,
           encode(sha256(convert_to(json_build_array(id,usuario_id,tentativa,expira_em,consumido_em)::text,'UTF8')),'hex')
      FROM contas_usuario_ticketgoogle
    UNION ALL
    SELECT 'sessao', encode(sha256(convert_to(session_key,'UTF8')),'hex'),
           encode(sha256(convert_to(json_build_array(session_key,session_data,expire_date)::text,'UTF8')),'hex')
      FROM django_session
    UNION ALL
    SELECT 'espaco', id::text,
           encode(sha256(convert_to(json_build_array(id,tipo,dono_id)::text,'UTF8')),'hex')
      FROM espacos_espaco
    UNION ALL
    SELECT 'membro', id::text,
           encode(sha256(convert_to(json_build_array(id,espaco_id,usuario_id,papel,criado_em)::text,'UTF8')),'hex')
      FROM espacos_membro
    UNION ALL
    SELECT 'convite', id::text,
           encode(sha256(convert_to(json_build_array(id,espaco_id,papel,token_hash,expira_em,usado_por_id,usado_em,revogado_em,criado_por_id)::text,'UTF8')),'hex')
      FROM espacos_convite
    UNION ALL
    SELECT 'conta', id::text,
           encode(sha256(convert_to(json_build_array(id,espaco_id,subgrupo_id,criador_id,pagador_id,visibilidade,status,criado_em,atualizado_em)::text,'UTF8')),'hex')
      FROM lancamentos_lancamento
    UNION ALL
    SELECT 'conta_acesso', id::text,
           encode(sha256(convert_to(json_build_array(id,lancamento_id,usuario_id)::text,'UTF8')),'hex')
      FROM lancamento_acesso
    UNION ALL
    SELECT 'recorrencia', id::text,
           encode(sha256(convert_to(json_build_array(id,espaco_id,subgrupo_id,criador_id,pagador_id,visibilidade,estado,criado_em,atualizado_em)::text,'UTF8')),'hex')
      FROM recorrencias_recorrencia
    UNION ALL
    SELECT 'recorrencia_acesso', id::text,
           encode(sha256(convert_to(json_build_array(id,recorrencia_id,usuario_id)::text,'UTF8')),'hex')
      FROM recorrencias_recorrencia_acesso
    UNION ALL
    SELECT 'documento_pdf', id::text,
           encode(sha256(convert_to(json_build_array(id,espaco_id,criado_por_id,destino_id,lancamento_id,vinculado_em,estado)::text,'UTF8')),'hex')
      FROM boletos_documentoboleto
    UNION ALL
    SELECT 'comprovante', id::text,
           encode(sha256(convert_to(json_build_array(id,lancamento_id,criado_por_id,pagamento_alvo_id,pagamento_id,vinculado_em,estado)::text,'UTF8')),'hex')
      FROM pagamentos_documentocomprovante
    UNION ALL
    SELECT 'notificacao', id::text,
           encode(sha256(convert_to(json_build_array(id,evento_id,destinatario_id,revogado_em)::text,'UTF8')),'hex')
      FROM notificacoes_notificacao
    UNION ALL
    SELECT 'sessao_push', fingerprint,
           encode(sha256(convert_to(json_build_array(fingerprint,usuario_id,revogada)::text,'UTF8')),'hex')
      FROM notificacoes_sessaopush
    UNION ALL
    SELECT 'instalacao_push', id::text,
           encode(sha256(convert_to(json_build_array(id,usuario_id,identificador,fingerprint,revogada)::text,'UTF8')),'hex')
      FROM notificacoes_instalacaopush
    UNION ALL
    SELECT 'inscricao_push', id::text,
           encode(sha256(convert_to(json_build_array(id,usuario_id,fingerprint,sessao_id,encode(segredo,'hex'),instalacao,geracao,ativa)::text,'UTF8')),'hex')
      FROM notificacoes_inscricaopush
    ORDER BY 1, 2
) TO STDOUT WITH CSV;
