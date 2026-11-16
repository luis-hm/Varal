import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { NoticeRow } from "./notice-row";

test("aviso não lido informa seu estado e permite a leitura", () => {
  const onClick = vi.fn();
  render(<NoticeRow title="Conta vencida" text="Veja a conta" time="8:00" unread="yes" tone="vencida" icon={<span>!</span>} onClick={onClick} />);
  const button = screen.getByRole("button", { name: /Conta vencida.*Veja a conta.*Não lido.*8:00/ });
  button.focus();
  expect(document.activeElement).toBe(button);
  fireEvent.click(button);
  expect(onClick).toHaveBeenCalledOnce();
});
