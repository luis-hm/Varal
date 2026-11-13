import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { StatusBadge, type Status } from "./status-badge";

const expected: Record<Status, [string, string]> = {
  aguardando: ["prendedor", "Aguardando boleto"],
  pendente: ["pendente", "Pendente"],
  vence: ["relogio", "Vence em breve"],
  vencida: ["alerta", "Vencida"],
  paga: ["pago", "Paga"],
  confirmada: ["comprovante", "Confirmada"],
  cancelada: ["fechar", "Cancelada"],
};

test("ca08/rnf09: every status shows the Doop icon and text, never colour alone", () => {
  for (const [status, [icon, text]] of Object.entries(expected)) {
    const { container, unmount } = render(<StatusBadge status={status as Status} />);
    const badge = container.firstElementChild as HTMLElement;
    expect(badge.dataset.status).toBe(status);
    expect(badge.querySelector("svg")?.dataset.name).toBe(icon);
    expect(badge.textContent).toBe(text);
    unmount();
  }
});
