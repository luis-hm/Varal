import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Folha } from "@/components/ui/folha";
import { RadioCard } from "@/components/ui/radio-card";
import { ordemPapeis, papeis } from "@/lib/grupos/papeis";
import { HouseCard } from "./house-card";
import { MemberRow } from "./member-row";

test("ca20: RadioCard is a native radio in an accessible group; state=on is the checked one", () => {
  const onChange = vi.fn();
  render(
    <div role="radiogroup" aria-label="Papel">
      {ordemPapeis.map((p) => (
        <RadioCard key={p} name="papel" value={p} state={p === "pagador" ? "on" : "off"} onChange={onChange} {...papeis[p]} />
      ))}
    </div>,
  );
  const radios = screen.getAllByRole("radio");
  expect(radios).toHaveLength(4);
  expect(screen.getByRole("radio", { name: /Pagador/ })).toHaveProperty("checked", true);
  fireEvent.click(screen.getByRole("radio", { name: /Observador/ }));
  expect(onChange).toHaveBeenCalled();
});

test("ca20: MemberRow shows the role as text, and is a button only when it opens management", () => {
  const { rerender } = render(<MemberRow role="pagador" initials="LB" name="Mãe" />);
  expect(screen.getByText("Pagador")).toBeTruthy();
  expect(screen.queryByRole("button")).toBeNull();
  const onClick = vi.fn();
  rerender(<MemberRow role="observador" initials="AN" name="Ana" onClick={onClick} />);
  fireEvent.click(screen.getByRole("button", { name: /Ana.*Observador/ }));
  expect(onClick).toHaveBeenCalled();
});

test("ca18: a house with no bills has no progress bar", () => {
  const { container, rerender } = render(<HouseCard label="Casa 1" caption="Sem contas ainda" />);
  expect(container.querySelector("i")).toBeNull();
  rerender(<HouseCard label="Casa 1" caption="R$ 1.479,60" caption-2="3 de 4 pagas" progress={75} />);
  expect(container.querySelector("i")).not.toBeNull();
});

test("ca19: Folha is a labelled dialog; Esc and the close buttons ask the parent to close; focus goes back", () => {
  const onClose = vi.fn();
  const opener = document.createElement("button");
  document.body.append(opener);
  opener.focus();
  const { rerender } = render(<Folha open onClose={onClose} title="Convidar para o grupo"><p>corpo</p></Folha>);
  const dialog = screen.getByRole("dialog", { name: "Convidar para o grupo" });
  expect(dialog.hasAttribute("open")).toBe(true);
  fireEvent(dialog, new Event("cancel", { cancelable: true }));
  expect(onClose).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getAllByRole("button", { name: "Fechar" })[0]);
  expect(onClose).toHaveBeenCalledTimes(2);
  rerender(<Folha open={false} onClose={onClose} title="Convidar para o grupo"><p>corpo</p></Folha>);
  expect(dialog.hasAttribute("open")).toBe(false);
  expect(document.activeElement).toBe(opener);
  opener.remove();
});
