// Doop: k0kB5dc-Vo / folha de 11 · Convidar membro (bkv_O9ohNO) + modal M05 (8XSFrkwy2d); no dedicated frame.
// COR-10 / ADR 0017: the admin decides, per category, what each member and observer may do.
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Folha } from "@/components/ui/folha";
import { ApiError, type Capacidade, type Casa, type GrupoDetalhe, type Permissoes } from "@/lib/grupos/client";
import { papeis } from "@/lib/grupos/papeis";
import { useAcoesGrupo, usePermissoes } from "@/lib/grupos/hooks";
import styles from "./grupo.module.css";

const ACOES: [Capacidade, string][] = [["ver", "Ver"], ["criar", "Cadastrar"], ["editar", "Editar"], ["pagar", "Pagar"], ["recorrencias", "Recorrências"]];
type Linha = Permissoes["membros"][number];

export function PermissoesFolha({ grupo, casa, onClose }: { grupo: GrupoDetalhe; casa: Casa | null; onClose: () => void }) {
  const atual = usePermissoes(grupo.id, casa?.id);
  const { salvarPermissoes } = useAcoesGrupo(grupo.id);
  // Edits start from what the server says now (role defaults while not personalised).
  const [rascunho, setRascunho] = useState<Permissoes | null>(null);
  const valor = rascunho ?? atual.data;
  const conflito = salvarPermissoes.error instanceof ApiError && salvarPermissoes.error.status === 409;
  const nomes = new Map(grupo.membros.map((m) => [m.id, m.nome || m.email || ""]));

  function fechar() {
    if (salvarPermissoes.isPending) return;
    setRascunho(null);
    salvarPermissoes.reset();
    onClose();
  }
  function mudar(membroId: string, acao: Capacidade, ligado: boolean) {
    if (!valor) return;
    setRascunho({
      ...valor,
      // Without "Ver" nothing else is allowed (the API refuses it too).
      membros: valor.membros.map((m): Linha => m.membro_id !== membroId ? m : acao === "ver" && !ligado ? { ...m, ver: false, criar: false, editar: false, pagar: false, recorrencias: false } : { ...m, [acao]: ligado }),
    });
  }
  function recarregar() {
    setRascunho(null);
    salvarPermissoes.reset();
    void atual.refetch();
  }
  function salvar() {
    if (!casa || !valor || salvarPermissoes.isPending) return;
    salvarPermissoes.mutate({ casa: casa.id, ...valor }, { onSuccess: () => fechar() });
  }

  return (
    <Folha
      open={!!casa}
      onClose={fechar}
      busy={salvarPermissoes.isPending}
      title="Quem pode fazer o quê"
      subtitle={casa ? `${casa.nome} · admins sempre podem tudo` : undefined}
      actions={<Button label={salvarPermissoes.isPending ? "Salvando…" : "Salvar"} onClick={salvar} disabled={!valor || salvarPermissoes.isPending || conflito} />}
    >
      {atual.isPending ? <p role="status">Carregando permissões…</p> : atual.error || !valor ? <p role="alert">Não foi possível carregar as permissões. <button type="button" className={styles.linkBtn} onClick={recarregar}>Tentar de novo</button></p> : (
        <div className={styles.form}>
          <label className={styles.interruptor}>
            <input type="checkbox" role="switch" checked={valor.personalizada} onChange={(e) => setRascunho({ ...valor, personalizada: e.target.checked })} disabled={salvarPermissoes.isPending} />
            Personalizar permissões desta categoria
          </label>
          {!valor.personalizada ? <p className={styles.nota}>Vale o padrão de cada papel: membros fazem tudo, observadores só veem.</p> : !valor.membros.length ? <p className={styles.nota}>Este grupo ainda não tem membros nem observadores.</p> : (
            <>
              <p className={styles.nota}>Quem criou ou paga uma conta sempre a vê. Contas com &quot;Só algumas pessoas&quot; continuam restritas. Quem entrar no grupo ou mudar de papel recebe o padrão do papel.</p>
              {valor.membros.map((m) => (
                <fieldset key={m.membro_id} className={styles.permissao}>
                  <legend>{nomes.get(m.membro_id) || "Pessoa"} <span>· {papeis[m.papel].title}</span></legend>
                  <div className={styles.permissaoAcoes}>
                    {ACOES.map(([acao, rotulo]) => (
                      <label key={acao}>
                        <input type="checkbox" checked={m[acao]} disabled={salvarPermissoes.isPending || (acao !== "ver" && !m.ver)} onChange={(e) => mudar(m.membro_id, acao, e.target.checked)} />
                        {rotulo}
                      </label>
                    ))}
                  </div>
                </fieldset>
              ))}
            </>
          )}
          {conflito ? <p role="alert" className={styles.erro}>Outra pessoa mudou estas permissões. Recarregue para ver a versão atual. <button type="button" className={styles.linkBtn} onClick={recarregar}>Recarregar</button></p> : salvarPermissoes.error && <p role="alert" className={styles.erro}>{salvarPermissoes.error.message}</p>}
        </div>
      )}
    </Folha>
  );
}
