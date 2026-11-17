-- Run only in quiescent lab source and restored clone, after journal replay.
-- Output may contain private finance data. Protect as 0600/tmpfs; log hashes only.
SET TIME ZONE 'UTC';
COPY (
    SELECT 'solicitacao' AS kind, id::text AS identity, row_to_json(s)::text AS state
    FROM solicitacoes_solicitacao AS s
    UNION ALL
    SELECT 'tombstone_nonce', id::text, row_to_json(t)::text
    FROM solicitacoes_tombstonenonce AS t
    UNION ALL
    SELECT 'par_pagamento', id::text, row_to_json(p)::text
    FROM solicitacoes_parpagamento AS p
    UNION ALL
    SELECT 'pin_pdf', reserva_id::text, row_to_json(pin)::text
    FROM boletos_pinpdf AS pin
    UNION ALL
    SELECT 'tentativa_copia_pdf', id::text, row_to_json(c)::text
    FROM boletos_tentativacopiapdf AS c
    ORDER BY 1, 2
) TO STDOUT WITH CSV;
