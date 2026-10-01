/**
 * TabelaPaginacao — Barra de paginação padrão do GL4 SGA-EDU.
 *
 * Uso:
 *   <TabelaPaginacao
 *     pagina={pagina}
 *     totalPaginas={totalPaginas}
 *     total={total}
 *     tamanho={tamanho}
 *     tamanhoOpcoes={[10, 25, 50]}
 *     onPaginaChange={setPagina}
 *     onTamanhoChange={setTamanho}
 *   />
 */
import React from "react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Typography } from "@/components/ui/typography";

export interface TabelaPaginacaoProps {
  pagina: number;
  totalPaginas: number;
  total: number;
  tamanho: number;
  tamanhoOpcoes?: number[];
  onPaginaChange: (pagina: number) => void;
  onTamanhoChange: (tamanho: number) => void;
  desabilitado?: boolean;
}

/** Gera a lista de páginas visíveis com reticências quando necessário. */
function gerarPaginas(atual: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const paginas: (number | "...")[] = [1];

  if (atual > 3) paginas.push("...");

  const inicio = Math.max(2, atual - 1);
  const fim = Math.min(total - 1, atual + 1);
  for (let i = inicio; i <= fim; i++) paginas.push(i);

  if (atual < total - 2) paginas.push("...");

  paginas.push(total);
  return paginas;
}

export const TabelaPaginacao: React.FC<TabelaPaginacaoProps> = ({
  pagina,
  totalPaginas,
  total,
  tamanho,
  tamanhoOpcoes = [10, 25, 50],
  onPaginaChange,
  onTamanhoChange,
  desabilitado = false,
}) => {
  const inicio = total === 0 ? 0 : (pagina - 1) * tamanho + 1;
  const fim = Math.min(pagina * tamanho, total);
  const paginas = gerarPaginas(pagina, totalPaginas);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t w-full min-w-0">
      {/* Indicador "Mostrando X-Y de Z" + seletor de tamanho */}
      <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 text-sm text-muted-foreground">
        <Typography variant="muted" className="text-xs whitespace-nowrap tabular-nums">
          Mostrando{" "}
          <span className="font-medium text-foreground">
            {inicio}–{fim}
          </span>{" "}
          de{" "}
          <span className="font-medium text-foreground">{total}</span> registros
        </Typography>

        <Separator orientation="vertical" className="hidden sm:block h-4" />

        <div className="flex items-center gap-1.5 whitespace-nowrap">
          <Typography variant="muted" className="text-xs">
            por página:
          </Typography>
          <Select
            value={String(tamanho)}
            onValueChange={(v) => onTamanhoChange(Number(v))}
            disabled={desabilitado}
          >
            <SelectTrigger className="h-8 w-[70px] text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {tamanhoOpcoes.map((op) => (
                <SelectItem key={op} value={String(op)} className="text-xs">
                  {op}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Navegação de páginas */}
      {totalPaginas > 1 && (
        <Pagination className="w-full sm:w-auto mx-0 justify-center sm:justify-end">
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                text="Anterior"
                onClick={() => onPaginaChange(Math.max(1, pagina - 1))}
                aria-disabled={pagina === 1 || desabilitado}
                className={
                  pagina === 1 || desabilitado
                    ? "pointer-events-none opacity-40"
                    : "cursor-pointer"
                }
              />
            </PaginationItem>

            {paginas.map((p, idx) =>
              p === "..." ? (
                <PaginationItem key={`ellipsis-${idx}`}>
                  <PaginationEllipsis />
                </PaginationItem>
              ) : (
                <PaginationItem key={p}>
                  <PaginationLink
                    isActive={p === pagina}
                    onClick={() => !desabilitado && onPaginaChange(p)}
                    className={desabilitado ? "pointer-events-none opacity-40" : "cursor-pointer"}
                  >
                    {p}
                  </PaginationLink>
                </PaginationItem>
              )
            )}

            <PaginationItem>
              <PaginationNext
                text="Próximo"
                onClick={() => onPaginaChange(Math.min(totalPaginas, pagina + 1))}
                aria-disabled={pagina === totalPaginas || desabilitado}
                className={
                  pagina === totalPaginas || desabilitado
                    ? "pointer-events-none opacity-40"
                    : "cursor-pointer"
                }
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
};
