import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Typography } from "@/components/ui/typography";
import { ThemeToggle } from "@/components/ThemeToggle";

export function SiteHeader({ title = "Painel Acadêmico" }: { title?: string }) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border/60 bg-card/50 backdrop-blur-xs px-4 lg:px-6 justify-between">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 h-4 data-vertical:self-auto"
        />
        <Typography variant="small" className="font-semibold text-foreground text-sm tracking-tight">
          {title}
        </Typography>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
      </div>
    </header>
  );
}
